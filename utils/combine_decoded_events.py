def parse_args():
    """Parses the command-line arguments."""

    description = """Given a json object containing mints/burns/swaps 
    (typically those for a particular pool in a particular date range), 
    prints the addresses called the mint or burn methods."""

    parser = ArgumentParser(description = description, allow_abbrev = False)
    parser.add_argument("path_to_folder_containing_decoded_events", 
        metavar = "path to folder of decoded events", type = str,
        help = "path to a folder that contains only text files containing decoded events")

    args = parser.parse_args()
    return vars(args)


def main():
    """Prints the addresses that called mint/burn.
    
    Given a json object containing mints/burns/swaps (typically those for a 
    particular pool in a particular date range), prints the addresses called 
    the mint or burn methods.
    """

    try:
        args = parse_args()
        decoded_events = json.load(open(args["path_to_decoded_events"], "r"))
        data = get_relevant_addresses(decoded_events)
        print(data)

    except Exception as ex:
        print(ex, file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
