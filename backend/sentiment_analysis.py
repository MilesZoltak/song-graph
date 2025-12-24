import os
import re
from transformers import pipeline
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional, Callable

# Load environment variables from .env file
load_dotenv()

def preprocess_lyrics_for_sentiment(lyrics: str) -> str:
    """
    Lyrics-specific preprocessing that preserves poetic meaning.
    Keeps stopwords and negations as they carry sentiment signal.
    
    Args:
        lyrics: Raw lyrics text string
    
    Returns:
        Preprocessed lyrics text
    """
    if not lyrics:
        return ""
    
    # Lowercase for consistency (RoBERTa is uncased)
    lyrics = lyrics.lower()
    
    # Remove structural annotations
    lyrics = re.sub(r'\[.*?\]', '', lyrics)  # [Chorus], [Verse 2], etc.
    lyrics = re.sub(r'\(x\d+\)', '', lyrics)  # (x2), (x3)
    lyrics = re.sub(r'\(repeat\)', '', lyrics, flags=re.IGNORECASE)
    
    # Collapse excessive whitespace but preserve stanza breaks (double newlines)
    lyrics = re.sub(r'\n{3,}', '\n\n', lyrics)  # Collapse 3+ newlines to 2
    lyrics = re.sub(r' +', ' ', lyrics)  # Collapse multiple spaces
    
    return lyrics.strip()


def split_into_stanzas(lyrics: str) -> List[str]:
    """
    Split lyrics into stanzas for granular sentiment analysis.
    
    Args:
        lyrics: Preprocessed lyrics text
    
    Returns:
        List of stanza strings
    """
    if not lyrics:
        return []
    
    # Split on double newlines (stanza breaks)
    stanzas = re.split(r'\n\n+', lyrics)
    
    # Filter out very short stanzas (< 10 words)
    # These are often just repeated words or song structure artifacts
    stanzas = [s.strip() for s in stanzas if len(s.split()) >= 10]
    
    # Fallback to full lyrics if no valid stanzas found
    return stanzas if stanzas else [lyrics]


def create_sentiment_classifier(model_name=None):
    """
    Create and return a sentiment analysis pipeline using Twitter RoBERTa.
    
    This model is trained on informal, metaphor-heavy text (Twitter), making it
    better suited for song lyrics than movie review models.
    
    Args:
        model_name: Optional model name (defaults to Twitter RoBERTa)
    
    Returns:
        Hugging Face sentiment analysis pipeline
    """
    model_name = model_name or 'cardiffnlp/twitter-roberta-base-sentiment-latest'
    
    try:
        # Initialize sentiment analysis pipeline
        sentiment_classifier = pipeline(
            "sentiment-analysis",
            model=model_name,
            device=-1  # Use CPU (-1) or GPU (0, 1, etc.)
        )
        return sentiment_classifier
    except Exception as e:
        raise RuntimeError(f"Failed to load sentiment model {model_name}: {e}")

def analyze_sentiment(lyrics: str, sentiment_classifier) -> Dict:
    """
    Analyze sentiment using stanza-level scoring and neutral-aware mapping.
    
    Returns raw score (0-1) that will be normalized at playlist level.
    Uses Twitter RoBERTa's 3-class output (neg/neutral/pos) for nuance.
    
    Args:
        lyrics: Lyrics text string
        sentiment_classifier: Hugging Face sentiment analysis pipeline
    
    Returns:
        Dictionary with sentiment analysis results
    """
    if not lyrics or not lyrics.strip():
        return {
            'sentiment_score': None,
            'sentiment_chunks': 0,
            'stanza_scores': []
        }
    
    # Preprocess lyrics
    processed = preprocess_lyrics_for_sentiment(lyrics)
    
    if not processed:
        return {
            'sentiment_score': None,
            'sentiment_chunks': 0,
            'stanza_scores': []
        }
    
    # Split into stanzas
    stanzas = split_into_stanzas(processed)
    
    if not stanzas:
        return {
            'sentiment_score': None,
            'sentiment_chunks': 0,
            'stanza_scores': []
        }
    
    # Score each stanza
    stanza_scores = []
    for stanza in stanzas:
        try:
            # Truncate to RoBERTa max length (512 tokens ≈ 400 words)
            result = sentiment_classifier(stanza[:2000])  # Character limit for safety
            
            if isinstance(result, list):
                result = result[0]
            
            label = result['label'].lower()
            score = result['score']
            
            # Map 3-class output to continuous valence
            # Twitter RoBERTa uses: negative, neutral, positive
            # or label_0 (neg), label_1 (neu), label_2 (pos)
            if 'negative' in label or label == 'label_0':
                # Negative: map confidence to 0.0
                valence = (1 - score) * 0.5  # Low valence
            elif 'neutral' in label or label == 'label_1':
                # Neutral: map to middle (0.5)
                valence = 0.5
            else:  # positive
                # Positive: map confidence to 1.0
                valence = 0.5 + (score * 0.5)  # High valence
            
            stanza_scores.append(valence)
            
        except Exception as e:
            # If a stanza fails, skip it but log for debugging
            continue
    
    if not stanza_scores:
        return {
            'sentiment_score': None,
            'sentiment_chunks': len(stanzas),
            'stanza_scores': []
        }
    
    # Average across stanzas (equal weight)
    raw_score = sum(stanza_scores) / len(stanza_scores)
    
    return {
        'sentiment_score': raw_score,
        'sentiment_chunks': len(stanzas),
        'stanza_scores': stanza_scores  # For debugging
    }

def analyze_sentiment_single(track: Dict, sentiment_classifier) -> Dict:
    """
    Analyze sentiment for a single track.
    
    Args:
        track: Track dictionary with 'lyrics' field
        sentiment_classifier: Hugging Face sentiment analysis pipeline
    
    Returns:
        Updated track dictionary with sentiment added
    """
    lyrics = track.get('lyrics', '')
    
    # Skip if sentiment already exists
    if 'sentiment_score' in track and track['sentiment_score'] is not None:
        return track
    
    # Skip if no lyrics
    if not lyrics:
        track['sentiment_score'] = None
        track['sentiment_chunks'] = 0
        track['stanza_scores'] = []
        return track
    
    try:
        # Analyze sentiment with stanza-level scoring
        sentiment_result = analyze_sentiment(lyrics, sentiment_classifier)
        
        # Add sentiment fields to track
        track.update(sentiment_result)
        
    except Exception as e:
        track['sentiment_score'] = None
        track['sentiment_chunks'] = 0
        track['stanza_scores'] = []
    
    return track

def add_sentiment_to_tracks(tracks: List[Dict], sentiment_classifier, progress_callback: Optional[Callable] = None, max_workers: int = 4):
    """
    Add sentiment analysis to all tracks in a list using parallel processing.
    
    Args:
        tracks: List of track dictionaries (must have 'lyrics' field)
        sentiment_classifier: Hugging Face sentiment analysis pipeline
        progress_callback: Optional callback function(current, total, stage, track) for progress updates
        max_workers: Maximum number of worker threads (default 4, lower than lyrics due to model inference)
    
    Returns:
        Updated tracks list with sentiment added
    """
    total_tracks = len(tracks)
    completed = 0
    
    # Create a dictionary to store results with index as key
    results_dict = {}
    
    def analyze_with_index(index: int, track: Dict) -> tuple:
        """Analyze sentiment and return tuple of (index, updated_track)"""
        return (index, analyze_sentiment_single(track.copy(), sentiment_classifier))
    
    # Use ThreadPoolExecutor to analyze in parallel
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_index = {
            executor.submit(analyze_with_index, i, track): i 
            for i, track in enumerate(tracks)
        }
        
        # Collect results as they complete
        for future in as_completed(future_to_index):
            index, updated_track = future.result()
            results_dict[index] = updated_track
            completed += 1
            
            # Call progress callback if provided
            if progress_callback:
                progress_callback(completed, total_tracks, 'sentiment', updated_track)
    
    # Return results in the same order as input
    return [results_dict[i] for i in range(len(tracks))]

