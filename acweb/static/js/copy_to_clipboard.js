async function copyToClipboard(text, textName) {
    try {
        await navigator.clipboard.writeText(text);
        console.log('Text copied to clipboard');
        alert(`${textName} copied to clipboard!\n\n${text}`);
    } catch (err) {
        console.error('Failed to copy text: ', err);
    }
}
