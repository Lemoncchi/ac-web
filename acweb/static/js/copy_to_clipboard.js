async function copyToClipboard(text, textName) {
    try {
        await navigator.clipboard.writeText(text);
        console.log('Text copied to clipboard');
        alert(`${textName}: ${text}\n${textName} copied to clipboard`);
    } catch (err) {
        console.error('Failed to copy text: ', err);
    }
}
