"""Moltbook API Client - HTTP wrapper for the Moltbook social network for AI agents."""
import re
import requests

from config import MOLTBOOK_API_KEY

BASE_URL = "https://www.moltbook.com/api/v1"
TIMEOUT = 15
MAX_CONTENT_LENGTH = 500  # Truncate external content to prevent prompt injection

# Number words for challenge solver
_WORD_TO_NUM = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
    "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19,
    "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50,
    "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90,
    "hundred": 100, "thousand": 1000,
}


def _truncate(text, max_len=MAX_CONTENT_LENGTH):
    """Truncate text to max length for safety."""
    if not text:
        return ""
    text = str(text)
    if len(text) > max_len:
        return text[:max_len] + "..."
    return text


def _dedup(word: str) -> str:
    """Collapse runs of same letter: 'foour' -> 'four', 'proodduct' -> 'product'."""
    if not word:
        return word
    result = [word[0]]
    for ch in word[1:]:
        if ch != result[-1]:
            result.append(ch)
    return "".join(result)


def _clean_challenge(text: str) -> str:
    """Remove obfuscation from challenge text (special chars, random case)."""
    cleaned = re.sub(r"[^a-zA-Z0-9\s]", "", text)
    cleaned = re.sub(r"\s+", " ", cleaned).strip().lower()
    return cleaned


def _match_number_word(token: str) -> int | None:
    """Try to match a token as a number word, with dedup fallback."""
    if token in _WORD_TO_NUM:
        return _WORD_TO_NUM[token]
    deduped = _dedup(token)
    if deduped in _WORD_TO_NUM:
        return _WORD_TO_NUM[deduped]
    return None


def _extract_numbers(text: str) -> list[float]:
    """Extract numbers from cleaned challenge text (word numbers + digits)."""
    tokens = text.split()
    numbers = []
    current_parts = []
    i = 0
    while i < len(tokens):
        token = tokens[i]
        # Try single token match (with dedup fallback)
        val = _match_number_word(token)
        if val is not None:
            current_parts.append(val)
            i += 1
            continue
        # Try joining with next token (handles splits like "twen ty" -> "twenty")
        if i + 1 < len(tokens):
            joined = token + tokens[i + 1]
            val = _match_number_word(joined)
            if val is not None:
                current_parts.append(val)
                i += 2
                continue
        # Try digit
        if re.match(r"^\d+(\.\d+)?$", token):
            if current_parts:
                numbers.append(_combine_parts(current_parts))
                current_parts = []
            numbers.append(float(token))
            i += 1
            continue
        # Not a number - emit accumulated parts
        if current_parts:
            numbers.append(_combine_parts(current_parts))
            current_parts = []
        i += 1
    if current_parts:
        numbers.append(_combine_parts(current_parts))
    return numbers


def _combine_parts(parts: list[int]) -> float:
    """Combine number word parts: [20, 3] -> 23, [5, 100, 20, 5] -> 525."""
    result = 0
    current = 0
    for p in parts:
        if p == 100:
            current = (current if current else 1) * 100
        elif p == 1000:
            current = (current if current else 1) * 1000
            result += current
            current = 0
        else:
            current += p
    result += current
    return float(result)


def _detect_operation(text: str, original: str = "") -> str:
    """Detect math operation from cleaned challenge text and original (uncleaned) text."""
    # Check original text for math symbols before cleaning removed them
    if original and "*" in original:
        return "multiply"
    # Dedup each token to handle obfuscated keywords like "proodduct" -> "product"
    deduped = " ".join(_dedup(t) for t in text.split())
    combined = text + " " + deduped  # Check both original and deduped
    if "product" in combined or "multiply" in combined or "multiplying" in combined or "times" in combined:
        return "multiply"
    if "divided" in combined or "quotient" in combined or "ratio" in combined:
        return "divide"
    if "slows" in combined or "loses" in combined:
        return "subtract"
    if "difference" in combined or "minus" in combined or "subtract" in combined or "less" in combined:
        if "new" in combined or "remain" in combined or "left" in combined or "result" in combined:
            return "subtract"
    # Default: addition (total force, sum, adds, combined, etc.)
    return "add"


def _solve_challenge(challenge_text: str) -> str:
    """Solve a Moltbook verification challenge. Returns answer as string with 2 decimals."""
    cleaned = _clean_challenge(challenge_text)
    numbers = _extract_numbers(cleaned)
    if not numbers:
        return "0.00"
    operation = _detect_operation(cleaned, original=challenge_text)
    if operation == "add":
        result = sum(numbers)
    elif operation == "multiply":
        result = 1.0
        for n in numbers:
            result *= n
    elif operation == "subtract":
        result = numbers[0] - sum(numbers[1:])
    elif operation == "divide":
        result = numbers[0] / numbers[1] if len(numbers) >= 2 and numbers[1] != 0 else numbers[0]
    else:
        result = sum(numbers)
    return f"{result:.2f}"


class MoltbookClient:
    """Simple HTTP client for the Moltbook API."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    def _configured(self) -> bool:
        return bool(self.api_key)

    def _request(self, method: str, path: str, **kwargs) -> dict:
        """Make an HTTP request. Returns parsed JSON or error dict."""
        if not self._configured():
            return {"success": False, "error": "Moltbook not configured (no API key)"}
        try:
            url = f"{BASE_URL}{path}"
            resp = requests.request(
                method, url, headers=self.headers, timeout=TIMEOUT, **kwargs
            )
            if resp.status_code == 429:
                data = resp.json() if resp.text else {}
                retry_min = data.get("retry_after_minutes", "")
                retry_sec = data.get("retry_after_seconds", "")
                hint = f"Retry after {retry_min} min" if retry_min else f"Retry after {retry_sec} sec"
                return {"success": False, "error": f"Rate limited. {hint}"}
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.Timeout:
            return {"success": False, "error": "Request timed out"}
        except requests.exceptions.ConnectionError:
            return {"success": False, "error": "Could not connect to Moltbook"}
        except requests.exceptions.HTTPError as e:
            try:
                body = e.response.json()
                return {"success": False, "error": body.get("error", str(e)), "hint": body.get("hint", "")}
            except Exception:
                return {"success": False, "error": str(e)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _handle_verification(self, data: dict) -> str | None:
        """If response requires verification, solve and verify. Returns error string or None on success."""
        if not data.get("verification_required"):
            return None
        verification = data.get("verification", {})
        code = verification.get("code", "")
        challenge = verification.get("challenge", "")
        if not code or not challenge:
            return "Verification required but no challenge provided."
        answer = _solve_challenge(challenge)
        verify_resp = self._request("POST", "/verify", json={
            "verification_code": code,
            "answer": answer,
        })
        if not verify_resp.get("success", False):
            return f"Verification failed: {verify_resp.get('error', 'Unknown')} (answer was {answer}, challenge: {challenge})"
        return None

    # ------------------------------------------------------------------ #
    # Profile
    # ------------------------------------------------------------------ #

    def get_my_profile(self) -> str:
        """Get your Moltbook profile."""
        data = self._request("GET", "/agents/me")
        if not data.get("success", False):
            return f"Error: {data.get('error', 'Unknown error')}"
        agent = data.get("agent", data.get("data", {}))
        return (
            f"Profile: {agent.get('name', '?')}\n"
            f"Description: {agent.get('description', 'N/A')}\n"
            f"Karma: {agent.get('karma', 0)}\n"
            f"Followers: {agent.get('follower_count', 0)}\n"
            f"Following: {agent.get('following_count', 0)}\n"
            f"Claimed: {agent.get('is_claimed', False)}"
        )

    # ------------------------------------------------------------------ #
    # Feed & Posts
    # ------------------------------------------------------------------ #

    def get_feed(self, sort: str = "hot", limit: int = 10) -> str:
        """Get personalized feed (subscribed submolts + followed agents)."""
        data = self._request("GET", f"/feed?sort={sort}&limit={limit}")
        if not data.get("success", False):
            return f"Error: {data.get('error', 'Unknown error')}"
        posts = data.get("posts", data.get("data", []))
        if not posts:
            return "Feed is empty. Try browsing global posts with sort='new'."
        return self._format_posts(posts, f"Feed ({sort})")

    def get_posts(self, sort: str = "hot", limit: int = 10) -> str:
        """Get global posts feed."""
        data = self._request("GET", f"/posts?sort={sort}&limit={limit}")
        if not data.get("success", False):
            return f"Error: {data.get('error', 'Unknown error')}"
        posts = data.get("posts", data.get("data", []))
        if not posts:
            return "No posts found."
        return self._format_posts(posts, f"Global posts ({sort})")

    def get_post(self, post_id: str) -> str:
        """Get a single post with its comments."""
        data = self._request("GET", f"/posts/{post_id}")
        if not data.get("success", False):
            return f"Error: {data.get('error', 'Unknown error')}"
        post = data.get("post", data.get("data", {}))
        comments_data = self._request("GET", f"/posts/{post_id}/comments?sort=top")
        comments = comments_data.get("comments", comments_data.get("data", []))

        result = (
            f"Post: {post.get('title', 'Untitled')}\n"
            f"Author: @{post.get('author', {}).get('name', '?')}\n"
            f"Submolt: m/{post.get('submolt', {}).get('name', '?')}\n"
            f"Upvotes: {post.get('upvotes', 0)} | Downvotes: {post.get('downvotes', 0)}\n"
            f"---\n"
            f"{_truncate(post.get('content', ''), 1000)}\n"
        )
        if comments:
            result += f"---\nComments ({len(comments)}):\n"
            for c in comments[:10]:
                author = c.get("author", {}).get("name", "?")
                content = _truncate(c.get("content", ""), 300)
                cid = c.get("id", "?")
                result += f"  [{cid}] @{author}: {content}\n"
        return result

    def create_post(self, submolt: str, title: str, content: str) -> str:
        """Create a text post on Moltbook (handles verification automatically)."""
        data = self._request("POST", "/posts", json={
            "submolt": submolt,
            "title": title,
            "content": content,
        })
        if not data.get("success", False):
            return f"Error posting: {data.get('error', 'Unknown')}. {data.get('hint', '')}"
        # Handle verification challenge
        verify_err = self._handle_verification(data)
        if verify_err:
            return f"Post created but verification failed: {verify_err}"
        post = data.get("post", data.get("data", {}))
        return f"Posted and verified! ID: {post.get('id', '?')} in m/{submolt}"

    # ------------------------------------------------------------------ #
    # Comments
    # ------------------------------------------------------------------ #

    def add_comment(self, post_id: str, content: str) -> str:
        """Add a comment to a post (handles verification automatically)."""
        data = self._request("POST", f"/posts/{post_id}/comments", json={
            "content": content,
        })
        if not data.get("success", False):
            return f"Error commenting: {data.get('error', 'Unknown')}. {data.get('hint', '')}"
        # Handle verification challenge
        verify_err = self._handle_verification(data)
        if verify_err:
            return f"Comment created but verification failed: {verify_err}"
        return f"Commented and verified on post {post_id}."

    def reply_to_comment(self, post_id: str, content: str, parent_id: str) -> str:
        """Reply to a specific comment (handles verification automatically)."""
        data = self._request("POST", f"/posts/{post_id}/comments", json={
            "content": content,
            "parent_id": parent_id,
        })
        if not data.get("success", False):
            return f"Error replying: {data.get('error', 'Unknown')}. {data.get('hint', '')}"
        # Handle verification challenge
        verify_err = self._handle_verification(data)
        if verify_err:
            return f"Reply created but verification failed: {verify_err}"
        return f"Replied and verified to comment {parent_id} on post {post_id}."

    # ------------------------------------------------------------------ #
    # Voting
    # ------------------------------------------------------------------ #

    def upvote_post(self, post_id: str) -> str:
        """Upvote a post."""
        data = self._request("POST", f"/posts/{post_id}/upvote")
        if not data.get("success", False):
            return f"Error upvoting: {data.get('error', 'Unknown')}"
        return f"Upvoted post {post_id}."

    def downvote_post(self, post_id: str) -> str:
        """Downvote a post."""
        data = self._request("POST", f"/posts/{post_id}/downvote")
        if not data.get("success", False):
            return f"Error downvoting: {data.get('error', 'Unknown')}"
        return f"Downvoted post {post_id}."

    # ------------------------------------------------------------------ #
    # Search
    # ------------------------------------------------------------------ #

    def search(self, query: str, search_type: str = "all", limit: int = 10) -> str:
        """Semantic search across Moltbook posts and comments."""
        data = self._request("GET", f"/search?q={query}&type={search_type}&limit={limit}")
        if not data.get("success", False):
            return f"Error searching: {data.get('error', 'Unknown')}"
        results = data.get("results", data.get("data", []))
        if not results:
            return f"No results for '{query}'."
        lines = [f"Search results for '{query}':"]
        for r in results[:limit]:
            rtype = r.get("type", "?")
            author = r.get("author", {}).get("name", "?")
            sim = r.get("similarity", 0)
            title = _truncate(r.get("title", ""), 100)
            content = _truncate(r.get("content", ""), 200)
            post_id = r.get("post_id", r.get("id", "?"))
            lines.append(
                f"---\n[{rtype}] post:{post_id} | @{author} | similarity:{sim:.2f}\n"
                f"{title}\n{content}"
            )
        return "\n".join(lines)

    # ------------------------------------------------------------------ #
    # Following
    # ------------------------------------------------------------------ #

    def follow_agent(self, agent_name: str) -> str:
        """Follow another agent."""
        data = self._request("POST", f"/agents/{agent_name}/follow")
        if not data.get("success", False):
            return f"Error following: {data.get('error', 'Unknown')}"
        return f"Now following @{agent_name}."

    def unfollow_agent(self, agent_name: str) -> str:
        """Unfollow an agent."""
        data = self._request("DELETE", f"/agents/{agent_name}/follow")
        if not data.get("success", False):
            return f"Error unfollowing: {data.get('error', 'Unknown')}"
        return f"Unfollowed @{agent_name}."

    # ------------------------------------------------------------------ #
    # Submolts
    # ------------------------------------------------------------------ #

    def subscribe_submolt(self, submolt_name: str) -> str:
        """Subscribe to a submolt."""
        data = self._request("POST", f"/submolts/{submolt_name}/subscribe")
        if not data.get("success", False):
            return f"Error subscribing: {data.get('error', 'Unknown')}"
        return f"Subscribed to m/{submolt_name}."

    def list_submolts(self) -> str:
        """List available submolts."""
        data = self._request("GET", "/submolts")
        if not data.get("success", False):
            return f"Error: {data.get('error', 'Unknown')}"
        submolts = data.get("submolts", data.get("data", []))
        if not submolts:
            return "No submolts found."
        lines = ["Available submolts:"]
        for s in submolts:
            name = s.get("name", "?")
            display = s.get("display_name", name)
            desc = _truncate(s.get("description", ""), 100)
            subs = s.get("subscriber_count", 0)
            lines.append(f"  m/{name} ({display}) - {subs} subscribers - {desc}")
        return "\n".join(lines)

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    def _format_posts(self, posts: list, header: str) -> str:
        """Format a list of posts into a readable string."""
        lines = [f"{header} - {len(posts)} posts:"]
        for p in posts:
            pid = p.get("id", "?")
            author = p.get("author", {}).get("name", "?")
            title = _truncate(p.get("title", "Untitled"), 100)
            upvotes = p.get("upvotes", 0)
            comments = p.get("comment_count", 0)
            submolt = p.get("submolt", {}).get("name", "?")
            content_preview = _truncate(p.get("content", ""), 150)
            lines.append(
                f"---\n[{pid}] @{author} in m/{submolt} | {upvotes} upvotes | {comments} comments\n"
                f"{title}\n{content_preview}"
            )
        return "\n".join(lines)


# Singleton instance
moltbook = MoltbookClient(MOLTBOOK_API_KEY)
