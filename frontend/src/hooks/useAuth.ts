import { useCallback, useState } from "react";
import { mockUser } from "@/data/mockData";
import type { User } from "@/types";

export function useAuth() {
  const [user, setUser] = useState<User | null>(null);
  const signIn = useCallback(async (email: string): Promise<User> => {
    const signedIn = { ...mockUser, email: email || mockUser.email };
    setUser(signedIn);
    return signedIn;
  }, []);
  const signOut = useCallback(() => setUser(null), []);
  return { user, signIn, signOut };
}
