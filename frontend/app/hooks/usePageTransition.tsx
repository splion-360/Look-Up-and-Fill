'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';

export function usePageTransition() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);

  const navigateWithTransition = async (destination: string) => {
    setIsLoading(true);
    
    const startTime = Date.now();
    
    // Simulate checking app response (replace with actual API call later)
    await new Promise(resolve => setTimeout(resolve, 100));
    
    const elapsed = Date.now() - startTime;
    const remainingTime = Math.max(0, 1500 - elapsed);
    
    setTimeout(() => {
      router.push(destination);
    }, remainingTime);
  };

  return {
    isLoading,
    navigate: navigateWithTransition,
  };
}