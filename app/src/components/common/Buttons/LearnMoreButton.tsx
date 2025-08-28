import React from 'react';
import WideButton from "./WideButton";
import {useLocation} from "wouter";

interface LearnMoreButtonProps {
    url: string;
}

const LearnMoreButton: React.FC<LearnMoreButtonProps> = (props) => {
    const [, navigate] = useLocation();
    return (
        <WideButton color="#141414" textColor={"#FFFFFF80"} text="📚 Как работает этот инструмент?"
                    buttonStyle={{
                        marginTop: 9,
                        borderRadius: 12,
                        fontSize: 17,
                        letterSpacing: -1,
                        minHeight: 55
                    }} onClick={() => navigate(props.url)}/>
    );
};

export default LearnMoreButton;