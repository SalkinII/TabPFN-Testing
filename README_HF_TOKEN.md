# Setting Up HuggingFace Token for TabPFN Authentication

TabPFN models require authentication to download from HuggingFace. This guide shows you how to set up your token.

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

#### Option A: Using dev.ps1 script (Recommended for Windows)

1. Copy the example file:
   ```powershell
   Copy-Item .env.example .env
   ```

2. Edit `.env` and add your token:
   ```
   HF_TOKEN=hf_your_actual_token_here
   ```

3. The `.env` file is already in `.gitignore`, so your token won't be committed.

4. Use the PowerShell script to start (it automatically loads .env):
   ```powershell
   .\dev.ps1 start
   ```
   
   Or for other operations:
   ```powershell
   .\dev.ps1 stop      # Stop container
   .\dev.ps1 restart   # Restart container
   .\dev.ps1 logs      # View logs
   .\dev.ps1 status    # Check status
   ```

#### Option B: Using PowerShell environment variable

Set the token as an environment variable before starting:

```powershell
$env:HF_TOKEN = "hf_your_actual_token_here"
docker-compose -f docker-compose.dev.yml up
```

#### Option C: Using docker-compose --env-file

```powershell
docker-compose --env-file .env -f docker-compose.dev.yml up
```

#### Option B: Set Environment Variable Directly

You can also pass the token directly when starting the container:

```bash
docker run -e HF_TOKEN=your_token_here -p 5006:5006 tabpfn-data-quality
```

Or with docker-compose, add it to the command:

```bash
HF_TOKEN=your_token_here docker-compose -f docker-compose.dev.yml up
```

### 4. Verify It's Working

After setting up the token, check the logs:

```bash
docker logs tabpfn-data-quality-dev | grep -i "huggingface\|token"
```

You should see:
- "HuggingFace token found - TabPFN models will authenticate"
- No authentication errors when models load

### 5. Test TabPFN Models

Run the data quality tests to verify TabPFN models are working:

```bash
docker exec tabpfn-data-quality-dev python tests/test_data_quality.py
```

If the token is working, you should see:
- TabPFN models initializing successfully
- No "Authentication error" messages
- Outlier detection using TabPFN instead of statistical fallback

## Troubleshooting

### Token Not Working

1. **Check token format**: Should start with `hf_`
2. **Verify token is valid**: Test at https://huggingface.co/settings/tokens
3. **Check model access**: Make sure you accepted the license at https://huggingface.co/Prior-Labs/tabpfn_2_5
4. **Check environment variable**: Run `docker exec tabpfn-data-quality-dev env | grep HF_TOKEN`

### Still Using Fallback Methods

If you see "statistical_fallback" in test output:
- The token might not be set correctly
- The model might not be accessible (check license acceptance)
- This is okay - the app will still work, just with statistical methods instead of TabPFN

## Security Notes

- Never commit your `.env` file (it's already in `.gitignore`)
- Never share your HuggingFace token publicly
- Use read-only tokens (not write tokens)
- Rotate tokens periodically

