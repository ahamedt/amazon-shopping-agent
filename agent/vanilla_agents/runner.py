from autonomous_amazon_agent import AmazonShoppingAgent
import colorama
from colorama import Fore, Style
import logging
import os
import textwrap

colorama.init()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("amazon_agent_cli.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def print_welcome_message():
    print(f"\n{Fore.CYAN}==================================================")
    print(f"       AMAZON SHOPPING AGENT ASSISTANT CLI")
    print(f"=================================================={Style.RESET_ALL}")
    print(f"\n{Fore.YELLOW}How to use this assistant:{Style.RESET_ALL}")
    print("- Type your shopping queries in natural language")
    print("- Ask follow-up questions about products")
    print("- Type 'exit', 'quit', or 'q' to end the conversation")
    print("- Type 'clear' to clear the conversation history")
    print("- Type 'help' to see these instructions again")
    print(f"\n{Fore.GREEN}Example queries:{Style.RESET_ALL}")
    print("- Find me a coffee maker under $100 with good reviews")
    print("- Show wireless headphones with noise cancellation")
    print("- What's the highest rated option from these results?")
    print(f"\n{Fore.CYAN}=================================================={Style.RESET_ALL}")
    print(f"{Fore.GREEN}Assistant is ready! What would you like to shop for today?{Style.RESET_ALL}\n")

def main():
    try:
        print_welcome_message()
        agent = AmazonShoppingAgent()
        logger.info("Starting Amazon Shopping Assistant")

        while True:
            user_input = input(f"{Fore.GREEN}You: {Style.RESET_ALL}")
            if user_input.lower() in ['exit', 'quit', 'q']:
                print(f"{Fore.YELLOW}Exiting Amazon Shopping Assistant. Goodbye!{Style.RESET_ALL}")
                break
            elif user_input.lower() == 'clear':
                agent.context.clear()
                os.system('cls' if os.name == 'nt' else 'clear')
                print_welcome_message()
                print(f"{Fore.BLUE}Assistant: Conversation history cleared.{Style.RESET_ALL}")
                continue
            elif user_input.lower() == 'help':
                print_welcome_message()
                continue
            if not user_input.strip():
                print(f"{Fore.YELLOW}Please enter a valid query.{Style.RESET_ALL}")
                continue
                
            try:
                print(f"{Fore.YELLOW}Processing your request...{Style.RESET_ALL}")
                response = agent.process_query(user_input)
                print(f"\n{Fore.BLUE}Assistant: {response}\n")
                
            except Exception as e:
                error_message = f"An error occurred: {str(e)}"
                print(f"{Fore.RED}Error: {error_message}{Style.RESET_ALL}")
                logger.error(error_message, exc_info=True)
                
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Program interrupted. Exiting Amazon Shopping Assistant.{Style.RESET_ALL}")
    except Exception as e:
        logger.critical(f"Unexpected error: {str(e)}", exc_info=True)
        print(f"{Fore.RED}A critical error occurred. Please check the logs.{Style.RESET_ALL}")
    finally:
        colorama.deinit()

        
if __name__ == "__main__":
    main()