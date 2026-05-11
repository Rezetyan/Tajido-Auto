import asyncio
from core.auth_manager import AuthManager
from core.post_manager import PostManager
from core.interaction_manager import InteractionManager
from utils.logger import logger
from utils.config import DRY_RUN, TARGET_URL
import os

async def main():
    logger.info("Starting Tajido Auto Script...")
    
    auth_manager = AuthManager()
    
    try:
        context = await auth_manager.get_context()
        page = await context.new_page()
        
        # Start API context for hybrid requests
        api_context = context.request
        
        post_manager = PostManager(page, dry_run=DRY_RUN)
        interaction_manager = InteractionManager(page, api_context, dry_run=DRY_RUN)
        
        # =================================================================
        # Instructions: Uncomment the tasks below to run them.
        # For a safe local rehearsal, run with:
        #   $env:TAJIDO_DRY_RUN="1"; python main.py
        # Dry-run fills and discovers items but skips submit/send/like clicks.
        # =================================================================
        
        # 1. Post a new image/text
        # sample_image = os.path.join("assets", "sample.png")
        # await post_manager.create_post("Hello World! This is an automated post.", sample_image)
        
        # 2. Reply to comments on own posts
        # await interaction_manager.reply_to_comments()
        
        # 3. Browse a specific tag and like posts
        # await interaction_manager.browse_and_like(
        #     target_url=TARGET_URL,
        #     max_likes=3,
        #     max_time_minutes=10,
        # )
        
        logger.info("All tasks completed successfully.")
        
    except Exception as e:
        logger.error(f"Critical error in main loop: {e}")
    finally:
        await auth_manager.close()
        logger.info("Browser closed. Exiting...")

if __name__ == "__main__":
    asyncio.run(main())
