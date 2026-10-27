import { createClient } from '@supabase/supabase-js';

let supabaseUrl = import.meta.env.VITE_SUPABASE_URL || import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
if (supabaseUrl && !supabaseUrl.startsWith('http://') && !supabaseUrl.startsWith('https://')) {
  supabaseUrl = `https://${supabaseUrl}`;
}
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.e30.local_token';

export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    persistSession: true,
    autoRefreshToken: true,
    detectSessionInUrl: true,
    storage: typeof window !== 'undefined' ? window.localStorage : undefined,
  },
});

export const DEFAULT_ORG_ID = '00000000-0000-0000-0000-000000000001';

let cachedOrgId: string | null = null;

export async function getOrganizationId(): Promise<string> {
  if (cachedOrgId) return cachedOrgId;

  try {
    const { data: { user } } = await supabase.auth.getUser();
    if (!user) return DEFAULT_ORG_ID;

    const { data: profile } = await supabase
      .from('user_profiles')
      .select('organization_id')
      .eq('user_id', user.id)
      .single();

    if (profile?.organization_id) {
      cachedOrgId = profile.organization_id;
      return profile.organization_id;
    }
  } catch (err) {
    console.warn('Could not retrieve organization ID from session, using fallback:', err);
  }

  return DEFAULT_ORG_ID;
}

export function setCachedOrganizationId(orgId: string | null) {
  cachedOrgId = orgId;
}
