'use client';

import * as React from 'react';

export interface PortfolioSessionData {
  fileName: string;
  uploadedAt: number;
  totalRows: number;
  missingSymbols: number;
  csvData?: any[];
}

const SESSION_KEY = 'portfolio_session';
const SESSION_VALID_KEY = 'portfolio_session_valid';

export function usePortfolioSession() {
  const [sessionData, setSessionData] = React.useState<PortfolioSessionData | null>(null);
  const [isLoading, setIsLoading] = React.useState(true);

  React.useEffect(() => {
    const isSessionValid = sessionStorage.getItem(SESSION_VALID_KEY);

    if (!isSessionValid) {
      sessionStorage.removeItem(SESSION_KEY);
      setIsLoading(false);
      return;
    }

    // Check for existing session data
    const stored = sessionStorage.getItem(SESSION_KEY);
    if (stored) {
      try {
        const parsed = JSON.parse(stored) as PortfolioSessionData;
        setSessionData(parsed);
      } catch (error) {
        // Invalid session data, clear it
        sessionStorage.removeItem(SESSION_KEY);
        sessionStorage.removeItem(SESSION_VALID_KEY);
      }
    }
    setIsLoading(false);
  }, []);

  const createSession = React.useCallback((data: Omit<PortfolioSessionData, 'uploadedAt'>) => {
    const sessionData: PortfolioSessionData = {
      ...data,
      uploadedAt: Date.now()
    };

    sessionStorage.setItem(SESSION_KEY, JSON.stringify(sessionData));
    sessionStorage.setItem(SESSION_VALID_KEY, 'true');
    setSessionData(sessionData);
  }, []);

  const clearSession = React.useCallback(() => {
    sessionStorage.removeItem(SESSION_KEY);
    sessionStorage.removeItem(SESSION_VALID_KEY);
    setSessionData(null);
  }, []);

  const hasValidSession = React.useCallback(() => {
    return sessionData !== null;
  }, [sessionData]);

  // Clear session validity flag on page unload to ensure fresh sessions
  React.useEffect(() => {
    const handleBeforeUnload = () => {
      sessionStorage.removeItem(SESSION_VALID_KEY);
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, []);

  return {
    sessionData,
    isLoading,
    createSession,
    clearSession,
    hasValidSession
  };
}