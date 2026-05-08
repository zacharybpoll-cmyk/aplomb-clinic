// Supabase client factory. Uses the service-role key — must only be called
// from server-side functions, never returned to the browser.

import { createClient } from '@supabase/supabase-js';

export function supabaseAdmin(env) {
  if (!env.SUPABASE_URL || !env.SUPABASE_SERVICE_ROLE_KEY) return null;
  return createClient(env.SUPABASE_URL, env.SUPABASE_SERVICE_ROLE_KEY, {
    auth: { persistSession: false, autoRefreshToken: false },
  });
}
