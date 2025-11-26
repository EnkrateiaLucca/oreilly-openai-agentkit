# ChatKit App Setup Guide

This guide will walk you through setting up and running your OpenAI ChatKit application.

## Prerequisites

- Node.js 20+ installed
- npm or yarn package manager
- OpenAI API key with ChatKit access
- A configured ChatKit workflow

## Step 1: Install Dependencies

```bash
npm install
```

This installs all required dependencies including:
- Next.js 15.5.4
- React 19.2.0
- @openai/chatkit-react (ChatKit SDK)

## Step 2: Configure Environment Variables

Create a `.env.local` file in the project root with your credentials:

```bash
# Your OpenAI API key (from platform.openai.com)
OPENAI_API_KEY=sk-proj-...

# Your ChatKit workflow ID (from your OpenAI workflow dashboard)
NEXT_PUBLIC_CHATKIT_WORKFLOW_ID=wf_...
```

### How to get your Workflow ID:
1. Go to [platform.openai.com](https://platform.openai.com)
2. Navigate to your ChatKit workflows
3. Copy the workflow ID (starts with `wf_`)

## Step 3: Verify Configuration

Check that your `.env.local` file exists and contains both values:

```bash
cat .env.local
```

You should see both `OPENAI_API_KEY` and `NEXT_PUBLIC_CHATKIT_WORKFLOW_ID` defined.

## Step 4: Run the Development Server

```bash
npm run dev
```

The app will start on:
- **Local**: http://localhost:3000
- **Network**: http://[your-ip]:3000

## Step 5: Test the Application

1. Open http://localhost:3000 in your browser
2. Wait for the "Loading assistant session..." message to complete
3. You should see the chat interface with:
   - Greeting: "How can I help you today?"
   - Starter prompts
   - Message input box
4. Try sending a message to test the chatbot

## Architecture Overview

```
app/
├── layout.tsx          # Root layout with ChatKit script loading
│                       # Includes crypto.randomUUID() polyfill
├── page.tsx            # Main page component
├── App.tsx             # Main app with color scheme handling
└── api/
    └── create-session/ # API route for creating ChatKit sessions
        └── route.ts

components/
├── ChatKitPanel.tsx    # ChatKit integration component
└── ErrorOverlay.tsx    # Error display component

lib/
└── config.ts           # ChatKit configuration (prompts, theme, etc.)

public/
└── crypto-polyfill.js  # Polyfill for older browsers
```

## Key Features

### 1. ChatKit Integration
The app uses OpenAI's ChatKit React SDK to provide:
- Real-time chat interface
- File attachment support
- Custom theming (light/dark mode)
- Client-side tool execution

### 2. Session Management
Sessions are created via the `/api/create-session` endpoint, which:
- Authenticates with your OpenAI API key
- Creates a new ChatKit session
- Returns a client secret for secure communication

### 3. Browser Compatibility
The app includes a `crypto.randomUUID()` polyfill for browsers that don't natively support this API, ensuring compatibility across:
- Chrome 92+
- Firefox 95+
- Safari 15.4+
- Edge 92+

### 4. Custom Tools
The app implements custom client-side tools:
- `switch_theme`: Toggle between light and dark mode
- `record_fact`: Save important information from conversations

## Customization

### Change Starter Prompts
Edit `lib/config.ts`:

```typescript
export const STARTER_PROMPTS = [
  {
    label: "Your custom prompt",
    prompt: "The full prompt text",
    icon: "circle-question"
  }
];
```

### Modify Theme Colors
In `lib/config.ts`, update the `getThemeConfig()` function:

```typescript
export function getThemeConfig(scheme: ColorScheme) {
  return {
    color: {
      grayscale: { hue: 220, tint: 6, shade: -4 },
      accent: { primary: "#0f172a", level: 1 }
    },
    radius: "round"
  };
}
```

### Enable/Disable Features
In `components/ChatKitPanel.tsx`:

```typescript
composer: {
  placeholder: PLACEHOLDER_INPUT,
  attachments: {
    enabled: true  // Set to false to disable file uploads
  },
},
threadItemActions: {
  feedback: false  // Set to true to enable feedback buttons
}
```

## Troubleshooting

### Issue: "Loading assistant session..." stuck forever

**Solution**: This was caused by `crypto.randomUUID()` not being available. The polyfill fix has been applied:
- `public/crypto-polyfill.js` provides the missing function
- Loaded in `app/layout.tsx` before ChatKit script

### Issue: "Set NEXT_PUBLIC_CHATKIT_WORKFLOW_ID in your .env.local file"

**Solution**:
1. Ensure `.env.local` exists
2. Add `NEXT_PUBLIC_CHATKIT_WORKFLOW_ID=wf_...` with your actual workflow ID
3. Restart the dev server

### Issue: "Failed to create ChatKit session"

**Solution**:
1. Verify your `OPENAI_API_KEY` is valid
2. Check that your API key has ChatKit access
3. Ensure your workflow ID is correct
4. Check the browser console for detailed error messages

### Issue: 404 on `/api/create-session`

**Solution**: The API route should be automatically available. If not:
1. Restart the dev server
2. Verify `app/api/create-session/route.ts` exists
3. Check for build errors in the terminal

## Production Deployment

### Build for Production

```bash
npm run build
npm start
```

### Environment Variables for Production

Set the same environment variables on your hosting platform:
- `OPENAI_API_KEY`
- `NEXT_PUBLIC_CHATKIT_WORKFLOW_ID`

### Recommended Hosting Platforms
- **Vercel** (optimized for Next.js)
- **Netlify**
- **AWS Amplify**
- **Railway**
- **Render**

## Security Considerations

1. **Never commit `.env.local`** - It's in `.gitignore` by default
2. **API Key Protection** - The `OPENAI_API_KEY` is only used server-side
3. **Client Secret** - ChatKit uses client secrets for secure session management
4. **HTTPS Required** - Always use HTTPS in production for secure communication

## Additional Resources

- [OpenAI ChatKit Documentation](https://platform.openai.com/docs/chatkit)
- [Next.js Documentation](https://nextjs.org/docs)
- [React Documentation](https://react.dev)

## Support

For issues or questions:
- Check the browser console for error messages
- Review the troubleshooting section above
- Contact OpenAI support for ChatKit-specific issues
- File issues on your project repository

---

**Happy Chatting! 🤖**
