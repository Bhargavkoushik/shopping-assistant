import json
import re
import sys


def has_destructive_rm(cmd_lower):
    words = cmd_lower.split()
    if not any(w == "rm" or w.endswith("/rm") or w.endswith("\\rm") for w in words):
        if "rm" not in cmd_lower:
            return False

    has_r = False
    has_f = False
    for word in words:
        if word.startswith("--"):
            if "recursive" in word:
                has_r = True
            elif "force" in word:
                has_f = True
        elif word.startswith("-") and not word.startswith("--"):
            flags = word[1:]
            if "r" in flags or "R" in flags:
                has_r = True
            if "f" in flags:
                has_f = True

    return has_r and has_f


def is_root_target(cmd_lower):
    words = cmd_lower.split()
    rm_idx = -1
    for i, w in enumerate(words):
        if w == "rm" or w.endswith("/rm") or w.endswith("\\rm"):
            rm_idx = i
            break
    if rm_idx == -1:
        return False
    targets = [w for w in words[rm_idx + 1 :] if not w.startswith("-")]
    for t in targets:
        if t in ("/", "/*", "c:\\", "c:\\*", "c:/", "c:/*"):
            return True
        if t.startswith("/") and any(
            sys_dir in t for sys_dir in ("/etc", "/var", "/usr", "/bin", "/sbin")
        ):
            return True
    return False


def main():
    try:
        # Read from stdin
        data = sys.stdin.read()
        if not data:
            sys.exit(0)

        payload = json.loads(data)
        tool_input = payload.get("tool_input", {})

        # Extract the command line
        command_line = tool_input.get("CommandLine", "") or tool_input.get(
            "command", ""
        )
        if not command_line and isinstance(tool_input, str):
            command_line = tool_input

        command_line = str(command_line).strip()
        cmd_lower = command_line.lower()

        # Check for mkfs
        if re.search(r"\bmkfs\b", cmd_lower):
            sys.stderr.write(
                f"Blocked: destructive command 'mkfs' detected in '{command_line}'.\n"
            )
            sys.exit(2)

        # Check for destructive rm targeting root
        if has_destructive_rm(cmd_lower) and is_root_target(cmd_lower):
            sys.stderr.write(
                f"Blocked: destructive command 'rm' targeting root detected in '{command_line}'.\n"
            )
            sys.exit(2)

        sys.exit(0)

    except Exception as e:
        # Fail closed for security
        sys.stderr.write(f"Error in validate_tool_call hook: {e!s}\n")
        sys.exit(2)


if __name__ == "__main__":
    main()
