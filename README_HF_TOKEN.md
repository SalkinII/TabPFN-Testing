# Setting Up HuggingFace Token for TabPFN Authentication

TabPFN models require authentication to download from HuggingFace. This guide shows you how to set up your token for production deployment.

## Steps

### 1. Get Your HuggingFace Token

1. Go to [HuggingFace Settings](https://huggingface.co/settings/tokens)
2. Click "New token"
3. Select "Read" token type
4. Copy the token (you'll only see it once!)

### 2. Accept Model License

1. Visit [TabPFN Model Page](https://huggingface.co/Prior-Labs/tabpfn_2_5)
2. Accept the terms of use
3. This is required before the token will work

### 3. Set Up Token for Docker

#### Option A: Using Environment Variable (Recommended)

Pass the token directly when starting the container:

```bash
docker run -e HF_TOKEN=your_token_here -p 5006:5006 tabpfn-data-quality
```

#### Option B: Using .env File with Docker Compose

1. Create a `.env` file in the project root:
   ```
   HF_TOKEN=hf_your_actual_token_here
   ```

2. The `.env` file is already in `.gitignore`, so your token won't be committed.

3. Start with docker-compose:
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

   Docker Compose will automatically load the `.env` file.

#### Option C: Using Environment Variable with Docker Compose

Set the token as an environment variable before starting:

```bash
export HF_TOKEN="hf_your_actual_token_here"
docker-compose -f docker-compose.prod.yml up -d
```

Or on Windows PowerShell:
```powershell
$env:HF_TOKEN = "hf_your_actual_token_here"
docker-compose -f docker-compose.prod.yml up -d
```

### 4. Verify It's Working

After setting up the token, check the container logs:

```bash
docker logs tabpfn-data-quality | grep -i "huggingface\|token"
```

Or view full logs:
```bash
docker logs tabpfn-data-quality
```

You should see:
- "HuggingFace token found - TabPFN models will authenticate"
- No authentication errors when models load

### 5. Test in Application

1. Upload a CSV file through the web interface
2. Check the quality assessment results
3. If TabPFN models are working, you'll see:
   - More sophisticated outlier detection
   - Enhanced anomaly detection
   - Better quality scoring

If the token is not set or invalid, the application will automatically fall back to statistical methods and still function correctly.

## Troubleshooting

### Token Not Working

1. **Check token format**: Should start with `hf_`
2. **Verify token is valid**: Test at https://huggingface.co/settings/tokens
3. **Check model access**: Make sure you accepted the license at https://huggingface.co/Prior-Labs/tabpfn_2_5
4. **Check environment variable**: 
   ```bash
   docker exec tabpfn-data-quality env | grep HF_TOKEN
   ```

### Still Using Fallback Methods

If the application is using statistical fallback methods:
- The token might not be set correctly
- The model might not be accessible (check license acceptance)
- This is okay - the app will still work, just with statistical methods instead of TabPFN models

You can verify by checking the logs for "statistical_fallback" messages.

## Security Notes

- Never commit your `.env` file (it's already in `.gitignore`)
- Never share your HuggingFace token publicly
- Use read-only tokens (not write tokens)
- Rotate tokens periodically
- For production deployments, consider using Docker secrets or your container orchestration platform's secret management
