export const formatToDayMonth = (date: Date) => {
    return date.toLocaleDateString('ru-RU', {
        day: '2-digit',
        month: '2-digit'
    });
}