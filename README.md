# Welcome to My GitHub Profile! 👋

```zig
const std = @import("std");

const AboutMe = struct {
    pub const name: []const u8 = "n0thhhing";
    pub const hobbies = [_][]const u8{
        "Coding",
        "BURNOUT",
        "art",
    };

    pub const languages = [_][]const u8{
        "zig",
        "c",
        "c++",
        "kotlin",
        "vim",
        "JavaScript",
        "lua",
        "python",
    };

    pub const frameworks = [_][]const u8{
        "Node.js",
        "typescript",
        "Bun",
        "hermes",
        "emscripten",
    };

    pub const tools = [_][]const u8{
        "Git",
        "NeoVim",
        "vsCode",
    };
};

const ActiveStatus = struct {
    pub const codes: []const u8 = "sometimes";
    pub const draws: []const u8 = "barely";
    pub const contributing: []const u8 = "never??";
    pub const exists: []const u8 = "conditionally";
};

pub fn main() void {
    std.debug.print("Thanks for visiting my GitHub profile! Feel free to explore my projects and contributions(if you find any)", .{});
}

```
