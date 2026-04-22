import asyncio
from core.auth_manager import AuthManager
from core.post_manager import PostManager
from core.interaction_manager import InteractionManager
from utils.logger import logger
import os

async def main():
    logger.info("Starting Tajido Auto Script...")
    
    auth_manager = AuthManager()
    
    try:
        context = await auth_manager.get_context()
        page = await context.new_page()
        
        # Start API context for hybrid requests
        api_context = context.request
        
        post_manager = PostManager(page)
        interaction_manager = InteractionManager(page, api_context)
        
        # =================================================================
        # ⚠️ Instructions: Uncomment the tasks below to run them.
        # Make sure to adjust the DOM selectors inside the manager classes
        # before running against the real website.
        # =================================================================
        
        # 1. Post a new image/text
        # sample_image = os.path.join("assets", "sample.png")
        # await post_manager.create_post("Hello World! This is an automated post.", sample_image)
        
        # 2. Reply to comments on own posts
        # await interaction_manager.reply_to_comments()
        
        # 3. Browse a specific tag and like posts
        # await interaction_manager.browse_and_like(tag="general", max_likes=3)
        
        logger.info("All tasks completed successfully.")
        
    except Exception as e:
        logger.error(f"Critical error in main loop: {e}")
    finally:
        await auth_manager.close()
        logger.info("Browser closed. Exiting...")

if __name__ == "__main__":
    asyncio.run(main())
