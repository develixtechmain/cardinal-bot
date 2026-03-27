export const valuesAreDifferent = (first: any, second: any): boolean => {
    if ((first != null && second == null) || (first == null && second != null)) {
        return true;
    }

    return first != null && second != null && first !== second;
};

const isMacOSDesktop = () => Telegram.WebApp.platform === "macos";
const isTelegramDesktop = () => Telegram.WebApp.platform === "tdesktop";
const isDesktop = () => isMacOSDesktop() || isTelegramDesktop();

export const openLink = (url: string) => {
    if (isDesktop()) {
        Telegram.WebApp.openLink(url);
    } else {
        Telegram.WebApp.openTelegramLink(url);
    }
};
