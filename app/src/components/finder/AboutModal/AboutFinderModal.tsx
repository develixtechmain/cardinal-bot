import styles from "./AboutFinderModal.module.css";
import {FC} from "react";

import {navigate} from "wouter/use-hash-location";

import AboutToolBlock from "../../common/AboutToolModal/AboutToolBlock";
import AboutToolModal from "../../common/AboutToolModal/AboutToolModal";
import AboutToolModalHeader from "../../common/AboutToolModal/AboutToolModalHeader";
import WideButton from "../../common/Buttons/WideButton";

interface AboutFinderModalProps {
    isOpen: boolean;
    onClose: () => void;
}

const AboutFinderModal: FC<AboutFinderModalProps> = ({isOpen, onClose}) => {
    const header = (
        <AboutToolModalHeader
            title={[{text: "ИИ лид"}, {text: "//", styles: {color: "#7211F8"}}, {text: "файндер"}]}
            description={
                "Система находит релевантные заказы для фрилансеров и экспертов, фильтрует их под твой профиль и показывает только те, что действительно нужны именно тебе."
            }
            infoTitle="Революция в поиске фриланс-заказов"
            infoDescription={[
                {
                    text: "Вместо сотен нерелевантных заявок, которые фрилансеры обычно перелистывают вручную и подбирают мусор, ИИ анализирует весь рынок фриланса и выдаёт только самые целевые заказы индивидуально под твой профиль."
                },
                {text: "Такой уровень точности и релевантности пока недоступен ни на одной другой платформе."}
            ]}
            icon={<img height="19px" width="38px" src="/assets/contact-catcher/about-icon.svg" alt=" " />}
            onClose={onClose}
        />
    );

    const aboutIcon = <img height="17px" width="33px" src="/assets/finder/about-icon.svg" alt=" " />;
    const eagleIcon = <img height="17px" width="33px" src="/assets/finder/about-eagle.svg" alt=" " />;
    const button = (
        <WideButton
            color="#BEF811"
            text="Начать ИИ парсинг заказов"
            textColor="black"
            onClick={() => navigate("/finder")}
            buttonStyle={{height: 47, borderRadius: 10, fontSize: 15, fontWeight: 500, lineHeight: 24, letterSpacing: "-0.03em"}}
        />
    );

    return (
        <AboutToolModal isOpen={isOpen} onClose={onClose} header={header}>
            <div className={styles.toolImage}>
                <img height="159px" width="345px" src="/assets/finder/about-tool.svg" alt=" " />
            </div>
            <div className={styles.title}>Как это работает</div>
            <div className={styles.toolBlocks}>
                <AboutToolBlock
                    icon={eagleIcon}
                    title={[
                        {text: "//", styles: {color: "#7211F8", bold: true}},
                        {text: "Умный брифинг", bold: true}
                    ]}
                    description={[
                        [{text: "Система не просит просто ввести ключевые слова, как у стандартных «парсеров». Это не парсер — это полноценный ИИ-агент."}],
                        [
                            {text: "ИИ задаёт индивидуальные вопросы и собирает детальный портрет твоей экспертизы:"},
                            {text: "услуги, опыт, ниша, стилистика работы, даже формат сотрудничества и т.д.", bold: true}
                        ]
                    ]}
                    background={<span className={styles.toolBackground}>01</span>}
                    backgroundBottom={24}
                    backgroundRight={-14}
                />
                <AboutToolBlock
                    icon={eagleIcon}
                    title={[
                        {text: "//", styles: {color: "#7211F8", bold: true}},
                        {text: "Постоянный indi-мониторинг", bold: true}
                    ]}
                    description={[
                        [{text: "ИИ отслеживает десятки источников — биржи, чаты, форумы, закрытые каналы и т.д."}],
                        [
                            {
                                text: "Но не просто «парсит», а каждый раз сопоставляет новые заказы именно с твоим портретом, а не просто с набором тегов. ИИ работает со смыслами и знает где сидят твои клиенты"
                            }
                        ]
                    ]}
                    background={<span className={styles.toolBackground}>02</span>}
                    backgroundBottom={24}
                />
                <AboutToolBlock
                    icon={eagleIcon}
                    title={[
                        {text: "//", styles: {color: "#7211F8"}, bold: true},
                        {text: "4-уровневая фильтрация", bold: true}
                    ]}
                    description={[
                        [{text: "Каждое сообщение, вакансия или заказ проходят через цепочку фильтров:"}],
                        [{text: "– отсев спама и нерелевантных объявлений"}],
                        [{text: "– глубокий анализ и сопоставление с твоими предпочтениями"}],
                        [{text: "– сопоставление с историей отправленных заказов и дополнительное обучение на её основе"}],
                        [{text: "– финальная проверка на соответствие твоему профилю."}]
                    ]}
                    background={<span className={styles.toolBackground}>03</span>}
                    backgroundBottom={24}
                    backgroundRight={4}
                />
                <AboutToolBlock
                    icon={aboutIcon}
                    title={[
                        {text: "//", styles: {color: "black"}, bold: true},
                        {text: "Мгновенный доступ к заказу", styles: {color: "black"}, bold: true}
                    ]}
                    description={[
                        [{text: "Секунды спустя после появления заказа в сети, ИИ проводит глубокий анализ и отправляет тебе результат:"}],
                        [{text: "– отфильтрованный заказ"}],
                        [{text: "– готовый текст отклика"}],
                        [{text: "– прямой контакт клиента."}]
                    ]}
                    background={
                        <span className={styles.toolBackground} style={{color: "#729017"}}>
                            04
                        </span>
                    }
                    backgroundBottom={86}
                    backgroundRight={2}
                    button={button}
                    backgroundColor="#BEF8117D"
                    borderColor="#BEF811"
                    headerColor="#BEF811"
                />
            </div>
        </AboutToolModal>
    );
};

export default AboutFinderModal;
