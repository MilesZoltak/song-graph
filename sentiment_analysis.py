import json
import os
import re
from transformers import pipeline
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def preprocess_lyrics(lyrics):
    """
    Preprocess lyrics to remove non-lyrical content and deduplicate repetition.
    
    Args:
        lyrics: Raw lyrics text string
    
    Returns:
        Preprocessed lyrics text
    """
    if not lyrics:
        return ""
    
    lines = lyrics.split('\n')
    processed_lines = []
    seen_sections = {}  # Track repeated sections
    
    for line in lines:
        line = line.strip()
        
        # Skip empty lines
        if not line:
            continue
        
        # Remove lines that are clearly spoken word intros/outros (quoted text, sermon-like)
        # Check for quotes at start/end or lines that are entirely in quotes
        if line.startswith('"') and line.endswith('"'):
            # Check if it's a long quote (likely intro/outro)
            if len(line) > 100:
                continue
        
        # Remove common non-lyrical markers
        if line.startswith('[') and line.endswith(']'):
            # Skip section markers like [Chorus], [Verse] etc. (we'll handle repetition differently)
            continue
        
        # Deduplicate: Track repeated sections
        # Normalize line for comparison (lowercase, remove punctuation)
        normalized = re.sub(r'[^\w\s]', '', line.lower())
        
        # If we've seen this exact line before, count occurrences
        if normalized in seen_sections:
            seen_sections[normalized] += 1
            # Only keep if it hasn't appeared more than twice
            if seen_sections[normalized] <= 2:
                processed_lines.append(line)
        else:
            seen_sections[normalized] = 1
            processed_lines.append(line)
    
    # Join back with newlines
    processed = '\n'.join(processed_lines)
    
    # Clean up extra whitespace
    processed = re.sub(r'\n{3,}', '\n\n', processed)  # Max 2 consecutive newlines
    processed = processed.strip()
    
    return processed

def chunk_text(text, chunk_size=300, overlap=50):
    """
    Split text into chunks with sentence-aware splitting and overlap.
    
    Args:
        text: Text to chunk
        chunk_size: Target words per chunk (default 300)
        overlap: Number of words to overlap between chunks (default 50)
    
    Returns:
        List of text chunks
    """
    if not text:
        return []
    
    # Split into sentences (rough approximation)
    # Split on newlines and periods followed by space
    sentences = re.split(r'(\n+|\.\s+)', text)
    
    # Recombine sentences with their separators
    combined_sentences = []
    for i in range(0, len(sentences) - 1, 2):
        if i + 1 < len(sentences):
            combined_sentences.append(sentences[i] + sentences[i + 1])
        else:
            combined_sentences.append(sentences[i])
    
    # If no sentence breaks found, split by newlines
    if len(combined_sentences) == 1:
        combined_sentences = text.split('\n')
    
    chunks = []
    current_chunk = []
    current_word_count = 0
    
    for sentence in combined_sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        
        word_count = len(sentence.split())
        
        # If adding this sentence would exceed chunk size, start a new chunk
        if current_word_count + word_count > chunk_size and current_chunk:
            # Save current chunk
            chunk_text = ' '.join(current_chunk)
            chunks.append(chunk_text)
            
            # Start new chunk with overlap (keep last overlap words)
            if overlap > 0 and len(current_chunk) > overlap:
                # Keep last overlap words for context
                overlap_words = current_chunk[-overlap:]
                current_chunk = overlap_words + [sentence]
                current_word_count = sum(len(w.split()) for w in overlap_words) + word_count
            else:
                current_chunk = [sentence]
                current_word_count = word_count
        else:
            current_chunk.append(sentence)
            current_word_count += word_count
    
    # Add final chunk
    if current_chunk:
        chunk_text = ' '.join(current_chunk)
        chunks.append(chunk_text)
    
    return chunks

def analyze_sentiment(lyrics, sentiment_classifier):
    """
    Analyze sentiment of lyrics text using chunking and aggregation.
    
    Args:
        lyrics: Lyrics text string
        sentiment_classifier: Hugging Face sentiment analysis pipeline
    
    Returns:
        Dictionary with sentiment analysis results including chunk count
    """
    if not lyrics or not lyrics.strip():
        return {
            'sentiment_label': None,
            'sentiment_score': None,
            'positive_score': None,
            'negative_score': None,
            'sentiment_chunks': 0
        }
    
    # Preprocess lyrics
    processed_lyrics = preprocess_lyrics(lyrics)
    
    if not processed_lyrics:
        return {
            'sentiment_label': None,
            'sentiment_score': None,
            'positive_score': None,
            'negative_score': None,
            'sentiment_chunks': 0
        }
    
    # Chunk the lyrics
    chunks = chunk_text(processed_lyrics, chunk_size=300, overlap=50)
    
    if not chunks:
        return {
            'sentiment_label': None,
            'sentiment_score': None,
            'positive_score': None,
            'negative_score': None,
            'sentiment_chunks': 0
        }
    
    # Analyze each chunk
    chunk_scores = []
    for chunk in chunks:
        try:
            result = sentiment_classifier(chunk)
            
            # Handle different output formats
            if isinstance(result, list):
                result = result[0]
            
            # Extract label and score
            label = result.get('label', '').lower()
            score = result.get('score', 0)
            
            # Normalize to positive_score (0-1 scale)
            if 'positive' in label or 'pos' in label:
                positive_score = score
            elif 'negative' in label or 'neg' in label:
                positive_score = 1 - score
            else:
                # For other labels, try to infer
                positive_score = score if score > 0.5 else 1 - score
            
            chunk_scores.append(positive_score)
            
        except Exception as e:
            # If a chunk fails, skip it
            print(f"    Warning: Error analyzing chunk: {e}")
            continue
    
    if not chunk_scores:
        return {
            'sentiment_label': None,
            'sentiment_score': None,
            'positive_score': None,
            'negative_score': None,
            'sentiment_chunks': len(chunks)
        }
    
    # Aggregate scores: simple average of all chunk scores
    avg_positive_score = sum(chunk_scores) / len(chunk_scores)
    avg_negative_score = 1 - avg_positive_score
    
    # Determine label based on aggregated score
    sentiment_label = 'positive' if avg_positive_score > 0.5 else 'negative'
    
    return {
        'sentiment_label': sentiment_label,
        'sentiment_score': avg_positive_score,  # Score from 0 (sad) to 1 (happy)
        'positive_score': avg_positive_score,
        'negative_score': avg_negative_score,
        'sentiment_chunks': len(chunks)
    }

def add_sentiment_to_playlist(playlist_file, sentiment_classifier):
    """
    Add sentiment analysis to all tracks in a playlist JSON file.
    
    Args:
        playlist_file: Path to the playlist JSON file
        sentiment_classifier: Hugging Face sentiment analysis pipeline
    
    Returns:
        Updated tracks list with sentiment added
    """
    # Read the playlist JSON
    with open(playlist_file, 'r', encoding='utf-8') as f:
        tracks = json.load(f)
    
    print(f"Processing {len(tracks)} tracks from {playlist_file}...")
    
    # Process each track
    for i, track in enumerate(tracks, 1):
        title = track.get('title', '')
        lyrics = track.get('lyrics', '')
        
        print(f"[{i}/{len(tracks)}] Analyzing: {title}")
        
        # Skip if sentiment already exists (and has chunks info, meaning it was analyzed with new method)
        if 'sentiment_label' in track and track['sentiment_label'] is not None and 'sentiment_chunks' in track:
            print("  ✓ Sentiment already analyzed, skipping...")
            continue
        
        # Skip if no lyrics
        if not lyrics:
            print("  ⚠ No lyrics available, skipping...")
            track['sentiment_label'] = None
            track['sentiment_score'] = None
            track['positive_score'] = None
            track['negative_score'] = None
            track['sentiment_chunks'] = 0
            continue
        
        try:
            # Analyze sentiment (now with chunking)
            sentiment_result = analyze_sentiment(lyrics, sentiment_classifier)
            
            # Add sentiment fields to track
            track.update(sentiment_result)
            
            chunks_info = f" ({sentiment_result['sentiment_chunks']} chunks)" if sentiment_result.get('sentiment_chunks', 0) > 1 else ""
            print(f"  ✓ Sentiment: {sentiment_result['sentiment_label']} "
                  f"(score: {sentiment_result['sentiment_score']:.3f}{chunks_info})")
            
        except Exception as e:
            print(f"  ✗ Error analyzing sentiment: {e}")
            track['sentiment_label'] = None
            track['sentiment_score'] = None
            track['positive_score'] = None
            track['negative_score'] = None
            track['sentiment_chunks'] = 0
    
    return tracks

def main():
    print("Loading sentiment analysis model...")
    print("(This may take a moment on first run as the model downloads)...")
    
    # Use a fast, accurate sentiment analysis model
    # distilbert-base-uncased-finetuned-sst-2-english is fast and good for binary sentiment
    # Alternative: "cardiffnlp/twitter-roberta-base-sentiment-latest" for more nuanced analysis
    model_name = os.getenv('SENTIMENT_MODEL', 'distilbert-base-uncased-finetuned-sst-2-english')
    
    try:
        # Initialize sentiment analysis pipeline
        sentiment_classifier = pipeline(
            "sentiment-analysis",
            model=model_name,
            device=-1  # Use CPU (-1) or GPU (0, 1, etc.)
        )
        print(f"✓ Model loaded: {model_name}\n")
    except Exception as e:
        print(f"Error loading model: {e}")
        print("\nTrying alternative model...")
        try:
            # Fallback to a different model
            sentiment_classifier = pipeline(
                "sentiment-analysis",
                model="cardiffnlp/twitter-roberta-base-sentiment-latest",
                device=-1
            )
            print("✓ Alternative model loaded\n")
        except Exception as e2:
            print(f"Error loading alternative model: {e2}")
            print("\nPlease check your internet connection and try again.")
            return
    
    # Get playlist file path
    playlists_dir = 'playlists'
    if not os.path.exists(playlists_dir):
        print(f"Error: {playlists_dir} directory not found!")
        print("Please run playlist_fetch.py first to create playlist JSON files.")
        return
    
    # List available playlist files
    playlist_files = [f for f in os.listdir(playlists_dir) if f.endswith('.json')]
    
    if not playlist_files:
        print(f"No JSON files found in {playlists_dir}/")
        print("Please run playlist_fetch.py first to create playlist JSON files.")
        return
    
    print("Available playlists:")
    for i, filename in enumerate(playlist_files, 1):
        print(f"  {i}. {filename}")
    
    # Let user choose a playlist
    choice = input("\nEnter playlist number (or 'all' to process all playlists): ").strip()
    
    if choice.lower() == 'all':
        files_to_process = [os.path.join(playlists_dir, f) for f in playlist_files]
    else:
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(playlist_files):
                files_to_process = [os.path.join(playlists_dir, playlist_files[idx])]
            else:
                print("Invalid selection!")
                return
        except ValueError:
            print("Invalid input!")
            return
    
    # Process each selected playlist
    for playlist_file in files_to_process:
        print(f"\n{'='*80}")
        print(f"Processing: {os.path.basename(playlist_file)}")
        print(f"{'='*80}\n")
        
        try:
            # Add sentiment analysis
            updated_tracks = add_sentiment_to_playlist(playlist_file, sentiment_classifier)
            
            # Save updated playlist with sentiment
            with open(playlist_file, 'w', encoding='utf-8') as f:
                json.dump(updated_tracks, f, indent=2, ensure_ascii=False)
            
            # Count statistics
            tracks_with_sentiment = sum(1 for t in updated_tracks if t.get('sentiment_label'))
            positive_tracks = sum(1 for t in updated_tracks if t.get('sentiment_label') == 'positive')
            negative_tracks = sum(1 for t in updated_tracks if t.get('sentiment_label') == 'negative')
            avg_score = sum(t.get('sentiment_score', 0) for t in updated_tracks if t.get('sentiment_score')) / max(tracks_with_sentiment, 1)
            
            print(f"\n{'='*80}")
            print(f"Completed: {os.path.basename(playlist_file)}")
            print(f"Tracks analyzed: {tracks_with_sentiment}/{len(updated_tracks)}")
            print(f"Positive: {positive_tracks} | Negative: {negative_tracks}")
            print(f"Average sentiment score: {avg_score:.3f}")
            print(f"{'='*80}\n")
            
        except Exception as e:
            print(f"Error processing {playlist_file}: {e}")

if __name__ == "__main__":
    main()

