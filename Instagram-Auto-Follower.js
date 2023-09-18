// Instagram Automation Script

// Constants
const TIMEOUT_DELAY = 10000; // Delay between actions (in milliseconds)
const SCROLL_DELAY = 300; // Delay for scrolling (in pixels)
const BATCH_SIZE = 5; // Number of users to follow in each batch
const MAX_ATTEMPTS = 3; // Maximum attempts to follow a user

// Function to click on the "Follow" button if available
function clickOnFollowButton(link) {
    if (link.firstChild.nodeValue === "Follow") {
        link.click();
        return true; // Successfully followed
    }
    return false; // Already followed or another state
}

// Function to scroll the followers/following dialog
async function scrollDialog(selector) {
    const dialog = document.querySelector('div[role="dialog"] .isgrP');
    dialog.scrollTop += SCROLL_DELAY;
    await timeoutPromise(TIMEOUT_DELAY);
}

// Function to follow a batch of users
async function followBatch(start, end) {
    for (let i = start; i < end; i++) {
        let attempts = 0;
        while (attempts < MAX_ATTEMPTS) {
            const success = clickOnFollowButton(list[i]);
            if (success) {
                console.log(`Successfully followed user ${i + 1}`);
                break;
            } else {
                console.log(`Failed to follow user ${i + 1}. Retrying...`);
                attempts++;
                await timeoutPromise(TIMEOUT_DELAY);
            }
        }
    }
}

// Main automation function
async function main() {
    for (let i = 0; i < list.length; i += BATCH_SIZE) {
        // Refresh the list of users
        list = document.querySelectorAll('.L3NKy');

        // Determine the end index for this batch
        const endIndex = Math.min(i + BATCH_SIZE, list.length);

        // Follow the current batch of users
        await followBatch(i, endIndex);

        // Scroll the dialog to load more users
        await scrollDialog("suggested");

        // Pause between batches to avoid detection
        await timeoutPromise(TIMEOUT_DELAY * 8); // Wait longer between batches
    }
}

// Start the automation
main();
