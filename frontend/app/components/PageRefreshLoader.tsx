'use client';

import * as React from 'react';
import PageTransitionLoader from './PageTransitionLoader';

export default function PageRefreshLoader({ children }: { children: React.ReactNode }) {
  const [isLoading, setIsLoading] = React.useState(true);

  React.useEffect(() => {
    // Show loader briefly on page load/refresh
    const timer = setTimeout(() => {
      setIsLoading(false);
    }, 500);

    return () => clearTimeout(timer);
  }, []);

  if (isLoading) {
    return <PageTransitionLoader />;
  }

  return <>{children}</>;
}