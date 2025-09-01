# Hugging Face Setup for SmartLearn

## Why Hugging Face?

Hugging Face provides free access to many open-source AI models, making it an excellent alternative to OpenAI for educational applications.

## Setup Steps

### 1. Get a Hugging Face API Key

1. Go to [Hugging Face](https://huggingface.co/)
2. Create a free account
3. Go to your profile → Settings → Access Tokens
4. Create a new token with "read" permissions
5. Copy the token

### 2. Configure Environment Variables

Add these to your `.env` file:

```bash
# Hugging Face Configuration
HUGGINGFACE_API_KEY=your_token_here
USE_HUGGINGFACE=true

# OpenAI (optional fallback)
OPENAI_API_KEY=your_openai_key_here
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

## How It Works

1. **Priority Order**: OpenAI → Hugging Face → Fallback Response
2. **Automatic Fallback**: If OpenAI fails, it tries Hugging Face
3. **Free Usage**: Hugging Face Inference API has generous free limits
4. **Educational Models**: Uses models optimized for conversational responses

## Available Models

The system currently uses:

- **Primary**: `microsoft/DialoGPT-medium` (good for educational responses)
- **Alternative**: Can be easily changed to other models

## Benefits

- ✅ **Free to use** (within API limits)
- ✅ **No credit card required**
- ✅ **Open source models**
- ✅ **Educational focus**
- ✅ **African context support**

## Limitations

- ⚠️ **Response quality** may vary compared to GPT-4
- ⚠️ **API rate limits** on free tier
- ⚠️ **Model availability** depends on Hugging Face

## Testing

1. Set `USE_HUGGINGFACE=true` in your `.env`
2. Restart the Flask app
3. Ask the AI Tutor a question
4. Check terminal logs for Hugging Face usage

## Troubleshooting

- **API errors**: Check your Hugging Face token
- **Rate limits**: Wait a few minutes between requests
- **Model issues**: The system will fallback to generic responses

## Next Steps

Consider exploring other Hugging Face models for:

- **Mathematics**: Specialized math models
- **Science**: Scientific explanation models
- **Language**: Multilingual support for African languages
