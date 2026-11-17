import Script from "next/script";

export const metadata = {
  title: "Herbaciarnia Liść — herbaty liściaste z dostawą",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pl">
      <body>
        <Script src="https://www.googletagmanager.com/gtm.js?id=GTM-TEST000" strategy="afterInteractive" />
        {children}
      </body>
    </html>
  );
}
