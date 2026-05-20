const rawApiUrl = process.env.REACT_APP_API_URL || '';

export const API_URL = rawApiUrl.endsWith('/') ? rawApiUrl.slice(0, -1) : rawApiUrl;
