import {create} from "zustand/index";
import {RefUser} from "../types/referral";

type ReferralStore = {
    refs: RefUser[] | undefined;
    setRefs: (refs: RefUser[]) => void;
}


export const useReferral = create<ReferralStore>((set) => ({
    refs: undefined,
    setRefs: (refs: RefUser[]) => set({refs}),
}))