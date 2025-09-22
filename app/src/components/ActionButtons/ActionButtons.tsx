import styles from "./ActionButtons.module.css";
import {CSSProperties, FC} from "react";

import {useLocation} from "wouter";

import {ActionButton} from "../../types/home";
import {hexToRgba} from "../../utils/color";
import WideButton from "../common/Buttons/WideButton";

import RefLogo from "../../assets/icons/crd-ref.svg";
import TariffLogo from "../../assets/icons/crd-tariff.svg";

interface ActionButtonsProps {
    buttons: ActionButton[];
    isSubscriptionExpired: boolean;
    isMoreThan3days: boolean;
}

const buttonStyles = {
    minHeight: 35,
    maxHeight: 35,
    fontFamily: "var(--font-ui)",
    fontSize: 13,
    fontWeight: 500,
    lineHeight: 18,
    letterSpacing: "-0.03em"
} as CSSProperties;

const logos = new Map([
    ["ref", RefLogo],
    ["tariff", TariffLogo]
]);

const ActionButtons: FC<ActionButtonsProps> = ({buttons, isSubscriptionExpired, isMoreThan3days}) => {
    const [, navigate] = useLocation();

    const getButtonColor = (button: ActionButton, background = true, withOpacity = false): string => {
        let color: string;
        if (button.buttonColor && !background) {
            color = button.buttonColor;
        } else if (isSubscriptionExpired) {
            color = button.expiredColor ?? button.color;
        } else if (isMoreThan3days) {
            color = button.longColor ?? button.color;
        } else {
            color = button.color;
        }

        return withOpacity ? hexToRgba(color, button.colorOpacity) : color;
    };

    const getContentColor = (button: ActionButton): string => {
        return button.contentColor || (isSubscriptionExpired || isMoreThan3days ? "#F2F2F2" : "#000000");
    };

    return (
        <div className={styles.actionButtons}>
            {buttons.map((button) => {
                const Logo = logos.get(button.id);

                return (
                    <div
                        key={button.id}
                        className={styles.actionBtn}
                        onClick={() => navigate(button.url)}
                        style={
                            {
                                "--color": button.borderColor || getButtonColor(button),
                                "--background-color": getButtonColor(button, true, true)
                            } as React.CSSProperties
                        }
                    >
                        {Logo ? (
                            <Logo
                                height="29px"
                                width="116px"
                                color={getButtonColor(button)}
                                style={{alignSelf: "flex-start", "--content-color": getContentColor(button)} as React.CSSProperties}
                            />
                        ) : (
                            <img height="29px" width="116px" style={{alignSelf: "flex-start"}} src={"/assets/crd-" + button.id + ".svg"} alt=" " />
                        )}
                        <WideButton
                            color={getButtonColor(button, false)}
                            text={button.buttonLabel}
                            onClick={() => navigate(button.url)}
                            buttonStyle={{color: getContentColor(button), ...buttonStyles}}
                        />
                    </div>
                );
            })}
        </div>
    );
};

export default ActionButtons;
