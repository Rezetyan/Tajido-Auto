from dataclasses import dataclass


@dataclass(frozen=True)
class PostSelectors:
    create_entry_links: tuple[str, ...] = (
        'a[href="#/create"]',
        'a:has-text("发帖子")',
        'button:has-text("发帖子")',
        "button.new-post-btn",
    )
    title_inputs: tuple[str, ...] = (
        "input#subject",
        'input[placeholder*="标题"]',
        'input[placeholder*="请输入标题"]',
    )
    text_editors: tuple[str, ...] = (
        '[contenteditable="true"].w-e-text',
        '[contenteditable="true"]',
        'textarea[placeholder*="正文"]',
        "textarea.post-editor",
        "textarea",
    )
    category_fields: tuple[str, ...] = (
        "input#communityId-columnId",
        '.ant-select:has(input#communityId-columnId)',
        '.ant-cascader:has(input#communityId-columnId)',
        'div:has(input#communityId-columnId)',
        'input[placeholder*="版区"]',
        'text=请选择版区',
    )
    category_primary_options: tuple[str, ...] = (
        '.ant-cascader-dropdown .ant-cascader-menu-item:has-text("{text}")',
        '.ant-select-dropdown .ant-cascader-menu-item:has-text("{text}")',
        '[role="menuitem"]:has-text("{text}")',
        'text={text}',
    )
    category_leaf_options: tuple[str, ...] = (
        '.ant-cascader-dropdown .ant-cascader-menu-item:has-text("{text}")',
        '.ant-select-dropdown .ant-cascader-menu-item:has-text("{text}")',
        '[role="menuitem"]:has-text("{text}")',
        'text={text}',
    )
    file_inputs: tuple[str, ...] = (
        'input[type="file"]',
    )
    submit_buttons: tuple[str, ...] = (
        'button[type="submit"]:has-text("发 布")',
        'button:has-text("发 布")',
        'button:has-text("发布")',
        "button.submit-post-btn",
    )


@dataclass(frozen=True)
class ReplySelectors:
    unread_reply_buttons: tuple[str, ...] = (
        '[data-unread="true"] button:has-text("回复")',
        '.unread button:has-text("回复")',
        "button.reply-btn.unread",
        'button:has-text("回复")',
    )
    reply_editors: tuple[str, ...] = (
        '[contenteditable="true"]',
        'textarea[placeholder*="回复"]',
        "textarea.reply-editor",
        "textarea",
    )
    send_buttons: tuple[str, ...] = (
        'button:has-text("发送")',
        'button:has-text("回复")',
        "button.send-reply-btn",
    )


@dataclass(frozen=True)
class LikeSelectors:
    post_links: tuple[str, ...] = (
        'a[href*="postId="]',
        'a[href*="/post/"]',
    )
    like_buttons: tuple[str, ...] = (
        'div.group:has(div[class*="like"])',
        '[data-action="like"]',
        'button:has-text("点赞")',
        '[aria-label*="点赞"]',
    )
    unliked_markers: tuple[str, ...] = (
        "text-tajido-gray-3",
        "bg-[#f3f4f5]",
        "like.png",
    )
    liked_markers: tuple[str, ...] = (
        "text-secondary-color",
        "like-hover.png",
    )


POST_SELECTORS = PostSelectors()
REPLY_SELECTORS = ReplySelectors()
LIKE_SELECTORS = LikeSelectors()
