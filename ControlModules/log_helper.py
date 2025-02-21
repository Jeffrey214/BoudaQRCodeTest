import logging

def setup_logging(log_file="deploy.log", level=logging.DEBUG):
    # Create a custom logger.
    logger = logging.getLogger("deploy_logger")
    logger.setLevel(level)
    
    # Avoid duplicate handlers if setup_logging is called multiple times.
    if not logger.handlers:
        # Create handlers: one for the log file, one for the console.
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.ERROR)  # Show only errors on console.
        
        # Create a formatter and add it to the handlers.
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers to the logger.
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    
    return logger
