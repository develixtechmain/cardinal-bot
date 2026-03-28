import styles from "./AboutContactCatcherModal.module.css";
import {CSSProperties, FC, useEffect, useRef, useState} from "react";

import {useLocation} from "wouter";

import AboutToolBlock from "../../common/AboutToolModal/AboutToolBlock";
import AboutToolModal from "../../common/AboutToolModal/AboutToolModal";
import AboutToolModalHeader from "../../common/AboutToolModal/AboutToolModalHeader";
import WideButton from "../../common/Buttons/WideButton";
import Delimiter from "../../common/Delimiter/Delimiter";

interface AboutCatcherModalProps {
    isOpen: boolean;
    onClose: () => void;
}

const AboutContactCatcherModal: FC<AboutCatcherModalProps> = ({isOpen, onClose}) => {
    const [, navigate] = useLocation();

    const imageRef = useRef<HTMLDivElement>(null);
    const [imageSpace, setImageSpace] = useState(0);

    useEffect(() => {
        const updateImageSpace = () => {
            if (imageRef.current) {
                const imgHeight = imageRef.current.offsetHeight;
                const imgBackgroundSpace = -imgHeight / 2.6;
                setImageSpace(imgBackgroundSpace);
            }
        };

        updateImageSpace();
        window.addEventListener("resize", updateImageSpace);

        return () => window.removeEventListener("resize", updateImageSpace);
    }, []);

    const handleImageLoad = () => {
        if (imageRef.current) {
            const imgHeight = imageRef.current.offsetHeight;
            const imgBackgroundSpace = -imgHeight / 2.6;
            setImageSpace(imgBackgroundSpace);
        }
    };

    const header = (
        <AboutToolModalHeader
            title={[{text: "Перехватчик"}, {text: "//", styles: {color: "#7211F8"}}, {text: "лидов"}]}
            description="Система которая перехватывает контакты заявок с сайтов и звонков конкурентов"
            infoTitle="Что это?"
            infoDescription={[
                {text: "Перехватчик — это технология, которая собирает контакты людей, звонящих или заходящих на сайты ваших конкурентов."},
                {text: "Это те самые клиенты, которые ищут ваш продукт прямо сейчас.", bold: true}
            ]}
        />
    );

    const webIcon = <img height="16px" width="33px" src="/assets/contact-catcher/about-web.svg" alt=" " />;
    const phoneIcon = <img height="17px" width="33px" src="/assets/contact-catcher/about-phone.svg" alt=" " />;

    const button = (
        <WideButton
            color="linear-gradient(to right, #7211F8, #430A92)"
            text="Перехватить заявки конкурентов"
            buttonStyle={{height: 47, borderRadius: 10, fontSize: 15, fontWeight: 500, lineHeight: 24, letterSpacing: "-0.03em"}}
            onClick={() => navigate("/subscription")}
        />
    );

    return (
        <AboutToolModal
            isOpen={isOpen}
            onClose={onClose}
            header={header}
            icon={<img height="19px" width="38px" src="/assets/contact-catcher/about-icon.svg" alt=" " />}
        >
            <div ref={imageRef} className={styles.toolImage}>
                <img height="336px" width="342px" src="/assets/contact-catcher/about-tool.svg" alt=" " onLoad={handleImageLoad} />
            </div>
            <div className={styles.title} style={{"--space": `${imageSpace}px`} as CSSProperties}>
                Как это работает
            </div>
            <div className={styles.benefits}>
                <div className={styles.benefit}>
                    <div className={styles.dot} />
                    <div className={styles.benefitText}>
                        <span style={{fontSize: 15, fontWeight: 700}}>Клиент у конкурента</span>
                        <span>Потенциальный лид заходит на сайт или звонит конкуренту → система фиксирует</span>
                    </div>
                </div>
                <div className={styles.benefit}>
                    <div className={styles.dot} />
                    <div className={styles.benefitText}>
                        <span style={{fontSize: 15, fontWeight: 700}}>Перехват данных</span>
                        <span>В течение 24 ч. система фиксирует действия потенциальных клиентов, которые взаимодействовали с ресурсами конкурентов.</span>
                    </div>
                </div>
                <div className={styles.benefit}>
                    <div className={styles.dot} />
                    <div className={styles.benefitText}>
                        <span style={{fontSize: 15, fontWeight: 700}}>Лиды у тебя</span>
                        <span>В личном кабинете вы получаете контакты потенциальных клиентов</span>
                    </div>
                </div>
            </div>
            <WideButton
                color="#7211F8"
                text="Подключить этот инструмент"
                onClick={() => navigate("/subscription")}
                buttonStyle={{height: 47, borderRadius: 10, fontSize: 15, fontWeight: 500, lineHeight: 24, letterSpacing: "-0.03em"}}
            />
            <Delimiter style={{backgroundColor: "#FFFFFF14", maxWidth: "100%", marginLeft: 2, marginRight: 2}} />
            <div className={styles.toolBlocks}>
                <AboutToolBlock
                    icon={webIcon}
                    title={[{text: "//", styles: {color: "#7211F8"}}, {text: "с сайтов конкурентов"}]}
                    description={[
                        [
                            {text: "//", styles: {color: "#7211F8"}},
                            {text: "Как:", bold: true},
                            {text: "собираете список сайтов конкурентов и добавляете их в систему"}
                        ],
                        [
                            {text: "//", styles: {color: "#7211F8"}},
                            {text: "Что получаешь:", bold: true},
                            {text: "до 20% посетителей сайтов конкурентов — в основном это входящий трафик из рекламы, которую они запускают"}
                        ]
                    ]}
                    button={button}
                />
                <AboutToolBlock
                    icon={phoneIcon}
                    title={[{text: "//", styles: {color: "#7211F8"}}, {text: "с номеров конкурентов"}]}
                    description={[
                        [
                            {text: "//", styles: {color: "#7211F8"}},
                            {text: "Как:", bold: true},
                            {text: "собираете номера телефонов отделов продаж конкурентов или номера, указанные на их сайтах, и добавляете в систему"}
                        ],
                        [
                            {text: "//", styles: {color: "#7211F8"}},
                            {text: "Что получаешь:", bold: true},
                            {text: "номера людей, которые звонят конкурентам, «горячие» контакты клиентов, уже ищущих услугу → высокая конверсия в заявки"}
                        ]
                    ]}
                    button={button}
                />
            </div>
        </AboutToolModal>
    );
};

export default AboutContactCatcherModal;
