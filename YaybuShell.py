if __name__ == "__main__":
    from yaybu.core.main import main
    # These imports are to force modules into site-packages.zip
    # (yay py2app)
    from yay import lextab
    from yay import parsetab
    main()

