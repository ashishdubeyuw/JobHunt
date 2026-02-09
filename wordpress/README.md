# WordPress Integration Guide

## Quick Embed (No Plugin)

Add this code to any WordPress page/post using the **Custom HTML** block:

```html
<iframe 
    src="http://YOUR_SERVER:8501" 
    width="100%" 
    height="850px" 
    frameborder="0"
    style="border-radius: 16px; box-shadow: 0 8px 32px rgba(0,0,0,0.2);">
</iframe>
```

---

## Plugin Installation

1. Upload the `job-matching-ai.php` file to `/wp-content/plugins/job-matching-ai/`
2. Activate the plugin in WordPress Admin → Plugins
3. Configure at Settings → Job Matching AI
4. Use shortcode anywhere: `[job_matching_ai]`

### Shortcode Options

| Shortcode | Description |
|-----------|-------------|
| `[job_matching_ai]` | Default embed |
| `[job_matching_ai height="600px"]` | Custom height |
| `[job_matching_ai glass="false"]` | No glass frame |
| `[job_matching_ai url="https://..."]` | Custom URL |

---

## Deployment Options

### Option 1: Local Network
```
http://192.168.x.x:8501
```

### Option 2: Streamlit Cloud (Free)
1. Push to GitHub
2. Connect at [share.streamlit.io](https://share.streamlit.io)
3. Use the generated URL

### Option 3: Reverse Proxy (nginx)
```nginx
location /jobmatcher/ {
    proxy_pass http://localhost:8501/;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
}
```
