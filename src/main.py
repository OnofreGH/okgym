from ui.ui import launch_app


if __name__ == "__main__":
    try:
        launch_app()
    except Exception as e:
        print(f"[ERROR]: {type(e).__name__} - {(e)}")