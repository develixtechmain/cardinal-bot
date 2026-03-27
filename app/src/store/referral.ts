import {create} from "zustand";

import {RefUser} from "../types/referral";

type ReferralStore = {refs: RefUser[] | undefined; setRefs: (refs: RefUser[]) => void};

export const useReferral = create<ReferralStore>((set) => ({refs: undefined, setRefs: (refs: RefUser[]) => set({refs})}));
