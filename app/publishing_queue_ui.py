from __future__ import annotations

from pathlib import Path

import streamlit as st

from app.publishing_queue import QUEUE_CONTENT_TYPES, QUEUE_PLATFORMS, QUEUE_STATUSES, PublishingQueue, QueueItem


def render_publishing_queue(database_path: Path) -> None:
    st.subheader("Publishing Queue")
    st.caption("Track creator work from idea to published output. This does not auto-publish anything.")

    queue = PublishingQueue(database_path)

    add_tab, review_tab = st.tabs(["Add item", "Review queue"])
    with add_tab:
        render_add_item(queue)
    with review_tab:
        render_review_queue(queue)


def render_add_item(queue: PublishingQueue) -> None:
    st.markdown("### Add queue item")
    title = st.text_input("Title", key="queue_title")
    platform = st.selectbox("Platform", QUEUE_PLATFORMS, key="queue_platform")
    content_type = st.selectbox("Content type", QUEUE_CONTENT_TYPES, key="queue_content_type")
    status = st.selectbox("Initial status", QUEUE_STATUSES, key="queue_status")
    priority = st.slider("Priority", min_value=1, max_value=5, value=3, help="1 is highest priority, 5 is lowest.")
    source_signal_id = st.number_input("Source signal ID", min_value=0, value=0, step=1)
    idea_id = st.number_input("Idea ID", min_value=0, value=0, step=1)
    blueprint_id = st.number_input("Blueprint ID", min_value=0, value=0, step=1)
    notes = st.text_area("Notes", key="queue_notes")

    if st.button("Add to Publishing Queue", type="primary"):
        try:
            item = queue.add_item(
                title=title,
                platform=platform,
                content_type=content_type,
                status=status,
                priority=priority,
                source_signal_id=int(source_signal_id) or None,
                idea_id=int(idea_id) or None,
                blueprint_id=int(blueprint_id) or None,
                notes=notes,
            )
            st.success(f"Added queue item #{item.id}.")
            st.session_state["last_queue_item_id"] = item.id
        except Exception as exc:  # noqa: BLE001
            st.error(str(exc))


def render_review_queue(queue: PublishingQueue) -> None:
    st.markdown("### Review queue")
    col1, col2, col3 = st.columns(3)
    status_filter = col1.selectbox("Status filter", ["all", *QUEUE_STATUSES], key="queue_status_filter")
    platform_filter = col2.selectbox("Platform filter", ["all", *QUEUE_PLATFORMS], key="queue_platform_filter")
    limit = col3.slider("Limit", min_value=10, max_value=200, value=50, step=10, key="queue_limit")

    items = queue.list_items(status=status_filter, platform=platform_filter, limit=limit)
    if not items:
        st.info("No queue items match the selected filters.")
        return

    st.dataframe(queue_rows(items), use_container_width=True, hide_index=True)
    selected_id = st.selectbox("Queue item ID", [item.id for item in items], key="queue_item_id")
    selected = queue.get_item(int(selected_id))
    if selected:
        st.markdown(selected.render())

    st.markdown("### Update status")
    new_status = st.selectbox("New status", QUEUE_STATUSES, key="queue_new_status")
    published_url = st.text_input("Published URL", key="queue_published_url")
    if st.button("Update queue item", key="queue_update_status"):
        try:
            updated = queue.update_status(int(selected_id), new_status, published_url=published_url or None)
            st.success(f"Updated queue item #{updated.id} to {updated.status}.")
        except Exception as exc:  # noqa: BLE001
            st.error(str(exc))


def queue_rows(items: list[QueueItem]) -> list[dict[str, object]]:
    return [
        {
            "id": item.id,
            "title": item.title,
            "platform": item.platform,
            "content_type": item.content_type,
            "status": item.status,
            "priority": item.priority,
            "source_signal_id": item.source_signal_id,
            "idea_id": item.idea_id,
            "blueprint_id": item.blueprint_id,
            "published_url": item.published_url,
            "updated_at": item.updated_at,
        }
        for item in items
    ]
