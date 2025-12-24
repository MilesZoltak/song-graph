export interface Track {
  title: string;
  artists: string[];
  album: string;
  album_art_url: string | null;
  album_release_date: string;
  duration_ms: number;
  duration_min: number;
  popularity: number;
  track_id: string;
  track_url: string;
  tempo?: number | null;
  key?: number | null;
  mode?: number | null;
  time_signature?: number | null;
  energy?: number | null;
  danceability?: number | null;
  acousticness?: number | null;
  instrumentalness?: number | null;
  liveness?: number | null;
  loudness?: number | null;
  speechiness?: number | null;
  valence?: number | null;
  audio_features_error?: string | null;
  lyrics?: string | null;
  lyrics_source?: string | null;
  genius_url?: string | null;
  sentiment_label?: string | null;
  sentiment_score?: number | null;
  positive_score?: number | null;
  negative_score?: number | null;
  sentiment_chunks?: number | null;
}

export interface PlaylistData {
  playlist_name: string;
  track_count: number;
  tracks: Track[];
  output_file?: string;
}

export interface PlotDataPoint extends Track {
  x: number;
  y: number;
}

export interface PlaylistMetadata {
  playlist_id: string;
  name: string;
  description: string | null;
  thumbnail_url: string | null;
  owner: string | null;
  total_tracks: number;
  public: boolean;
  followers: number;
}

