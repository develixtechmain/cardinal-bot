export const getDaysLeftEnding = (days: number) => {
    const lastDigit = days % 10;
    const lastTwoDigits = days % 100;

    if (lastDigit === 1 && lastTwoDigits !== 11) {
        return "день";
    } else if (lastDigit >= 2 && lastDigit <= 4 && (lastTwoDigits < 10 || lastTwoDigits >= 20)) {
        return "дня";
    } else {
        return "дней";
    }
};
