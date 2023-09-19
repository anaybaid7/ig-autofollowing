// Constants
const TIMEOUT_DELAY = 10000;
const SCROLL_DELAY = 300;
const BATCH_SIZE = 5;
const MAX_ATTEMPTS = 3;

// Function to click on the "Follow" button if available
function clickOnFollowButton(link) {
    if (link.firstChild.nodeValue === "Follow") {
        link.click();
        return true;
    }
    return false;
}

// Function to like a post
function likePost(post) {
    const likeButton = post.querySelector('.like-button');
    if (likeButton) {
        likeButton.click();
        return true;
    }
    return false;
}

// Function to comment on a post
function commentOnPost(post, comment) {
    const commentInput = post.querySelector('.comment-input');
    const submitButton = post.querySelector('.comment-submit');
    if (commentInput && submitButton) {
        commentInput.value = comment;
        submitButton.click();
        return true;
    }
    return false;
}

// Function to scroll the followers/following dialog
async function scrollDialog(selector) {
    const dialog = document.querySelector('div[role="dialog"] .isgrP');
    dialog.scrollTop += SCROLL_DELAY;
    await timeoutPromise(TIMEOUT_DELAY);
}

// Function to follow a batch of users and interact with their posts
async function followAndInteractWithUsers(start, end) {
    for (let i = start; i < end; i++) {
        let attempts = 0;
        while (attempts < MAX_ATTEMPTS) {
            const user = list[i];
            const success = clickOnFollowButton(user);
            if (success) {
                console.log(`Successfully followed user ${i + 1}`);
                likePost(user);
                commentOnPost(user, "Great content!");
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
        list = document.querySelectorAll('.L3NKy');
        const endIndex = Math.min(i + BATCH_SIZE, list.length);
        followAndInteractWithUsers(i, endIndex);
        await scrollDialog("suggested");
        await timeoutPromise(TIMEOUT_DELAY * 8); // Longer pause between batches
    }
}

// Start the automation
main();
