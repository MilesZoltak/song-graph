interface PlaylistEmbedProps {
  playlistId: string | null;
}

function PlaylistEmbed({ playlistId }: PlaylistEmbedProps) {
  if (!playlistId) return null;

  const embedUrl = `https://open.spotify.com/embed/playlist/${playlistId}?utm_source=generator`;

  return (
    <div className="w-full max-w-2xl mx-auto mb-8">
      <div className="bg-white rounded-lg shadow-md p-4">
        <iframe
          data-testid="embed-iframe"
          style={{ borderRadius: '12px' }}
          src={embedUrl}
          width="100%"
          height="352"
          frameBorder="0"
          allowFullScreen={true}
          allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture"
          loading="lazy"
          title="Spotify Playlist"
        ></iframe>
      </div>
    </div>
  );
}

export default PlaylistEmbed;

