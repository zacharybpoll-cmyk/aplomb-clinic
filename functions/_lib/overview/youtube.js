// Command Center — YouTube public channel stats via YouTube Data API v3 with
// an API key only (no OAuth). Subscribers, lifetime views, video count, and
// the latest uploads' view counts. Deeper analytics (impressions, watch time,
// YouTube's own CTR) need OAuth — that is Phase 2, intentionally not here.
//
// Env: YOUTUBE_API_KEY + YOUTUBE_CHANNEL_ID ("UC…" id or "@handle").
// Returns { connected:false } when unconfigured so the tile shows
// "Not connected" rather than erroring.

const BASE = 'https://www.googleapis.com/youtube/v3';

async function yt(path, params, key) {
  const qs = new URLSearchParams({ ...params, key }).toString();
  const r = await fetch(`${BASE}/${path}?${qs}`);
  const body = await r.json().catch(() => ({}));
  if (!r.ok) {
    const msg = body?.error?.message || `HTTP ${r.status}`;
    throw new Error(`YouTube ${path}: ${msg}`);
  }
  return body;
}

export async function getYouTubeMetrics(env) {
  const key = env.YOUTUBE_API_KEY;
  const channel = env.YOUTUBE_CHANNEL_ID;
  if (!key || !channel) return { connected: false };

  // Resolve channel by id or @handle.
  const sel = channel.startsWith('UC')
    ? { id: channel }
    : { forHandle: channel.replace(/^@/, '') };
  const chan = await yt('channels', { part: 'snippet,statistics,contentDetails', ...sel }, key);
  const item = (chan.items || [])[0];
  if (!item) throw new Error('YouTube: channel not found (check YOUTUBE_CHANNEL_ID)');

  const s = item.statistics || {};
  const uploads = item.contentDetails?.relatedPlaylists?.uploads;

  let recent = [];
  if (uploads) {
    const pl = await yt('playlistItems', { part: 'contentDetails', playlistId: uploads, maxResults: '5' }, key);
    const ids = (pl.items || []).map((i) => i.contentDetails?.videoId).filter(Boolean);
    if (ids.length) {
      const vids = await yt('videos', { part: 'snippet,statistics', id: ids.join(',') }, key);
      recent = (vids.items || []).map((v) => ({
        id: v.id,
        title: v.snippet?.title || '',
        published_at: v.snippet?.publishedAt || null,
        views: Number(v.statistics?.viewCount || 0),
        likes: Number(v.statistics?.likeCount || 0),
      }));
    }
  }

  return {
    connected: true,
    channel: {
      title: item.snippet?.title || '',
      subscribers: s.hiddenSubscriberCount ? null : Number(s.subscriberCount || 0),
      total_views: Number(s.viewCount || 0),
      video_count: Number(s.videoCount || 0),
    },
    recent_videos: recent,
  };
}
