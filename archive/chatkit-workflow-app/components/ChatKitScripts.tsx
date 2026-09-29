"use client";

import Script from "next/script";

export function ChatKitScripts() {
  return (
    <>
      {/* Load crypto polyfill before ChatKit to ensure compatibility */}
      <Script
        src="/crypto-polyfill.js"
        strategy="beforeInteractive"
      />
      <Script
        src="https://cdn.platform.openai.com/deployments/chatkit/chatkit.js"
        strategy="beforeInteractive"
        onLoad={() => {
          if (typeof window !== 'undefined') {
            window.dispatchEvent(new Event('chatkit-script-loaded'));
          }
        }}
        onError={() => {
          if (typeof window !== 'undefined') {
            window.dispatchEvent(new CustomEvent('chatkit-script-error', {
              detail: 'Failed to load ChatKit script'
            }));
          }
        }}
      />
    </>
  );
}
