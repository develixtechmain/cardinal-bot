import {FC} from "react";

import WideButton from "./WideButton";

interface LearnMoreButtonProps {
    showModal: () => void;
}

const LearnMoreButton: FC<LearnMoreButtonProps> = ({showModal}) => {
    return (
        <WideButton
            color="#141414"
            textColor={"#FFFFFF80"}
            text="📚 Как работает этот инструмент?"
            buttonStyle={{marginTop: 9, borderRadius: 12, fontSize: 17, letterSpacing: -1, minHeight: 55}}
            onClick={showModal}
        />
    );
};

export default LearnMoreButton;
