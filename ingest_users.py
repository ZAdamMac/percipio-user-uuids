"""
A simplistic tool to quickly consume the user-management service and generate a
user listing that includes UUIDs. Custom attributes aren't handled as the main
goal is just to get enough data to merge the UUIDs into other reports/listings.

If changes are required to this file email zac.macewen@skillsoft.com - this
script is version-controlled away from this machine and the changes would need
to be accounted for. If you're familiar, submit a PR at the github repo
zadammac/percipio-user-uuids.
"""

import argparse
import csv
from datetime import date
import http.client as web
import json
import os.path

__version__ = "1.0"

#  Normally, you would never create your classes and functions and runtime all in one package like this.
#  However, this task is pretty straight-forward.


class Namespace(object):  # That's it, it really is THAT simple
    pass                  # This is a terrible coding habit, don't do it.


def display_output(namespace):
    print(namespace.path_output)


def display_welcome():
    print("Welcome to the UUID Retrieval Tool, Version %s" % __version__)


def obtain_raw_json(namespace):
    """ There's a slight trick to this. We need to call down the right endpoint
    iteratively, exactly the same way we do for content management requests.

    :param namespace: The global namespace controller.
    :return:
    """
    ns = namespace
    if ns.use_eu:  # These are hard-coded values because they're core to our REST API offering
        api_fqdn = "dew1-api.percipio.com"
    else:
        api_fqdn = "api.percipio.com"

    print("Okay, using %s" % api_fqdn)

    # We need to iterate on this endpoint, which can get a little gross
    pulling = True
    offset = 0
    request_base_path = "/user-management/v1/organizations/%s/users?offset=" % ns.org_id
    ns.data_store = []  # Instead of some number of lists of dictionaries, let's just have one.

    while pulling:
        connection = web.HTTPSConnection(api_fqdn)  # Need a fresh connection for each.
        this_request = request_base_path + str(offset)  # we can just cat our internal offset timer into the query
        connection.request("GET", this_request, headers={"Authorization": ("Bearer " + ns.bearer)})
        response = connection.getresponse()
        if response.status != 200:
            print("Recieved an error, exiting")
            exit(1)
        if ns.debug:
            print("Offset: %s - %s" % (offset, response.status))
        this_response = json.loads(response.read())
        connection.close()
        # at this point, "this_response" should be a list of dicts
        if not len(this_response) == 0:
            for each in this_response:
                ns.data_store.append(each)
            offset += 1000  # We increment by 1000 each time because the max value of max is 1000.
        else:  # An empty array means we get nothing!
            pulling = False
            break

    print("Found %s user records via the API" % len(ns.data_store))
    return ns


def parse_args(namespace):
    """Parse arguments and return the modified namespace object"""
    ns = namespace
    parser = argparse.ArgumentParser(description="Ingest the User-Management Service to get "
                                                 "a CSV Report of All User UUIDS")
    parser.add_argument('--eu', help="Query the EUDC rather than USDC.",
                        action="store_true")
    parser.add_argument('-i', help="The OrgUUID for the client in question.", required=True,
                        action="store")
    parser.add_argument('--debug', help="Increase output verbosity.", action="store_true")
    parser.add_argument('-b', help="A valid bearer token", required=True, action="store")
    parser.add_argument('-o', help="Filename for the output file. Does not accept paths."
                                   " If none, the timestamp will be used.",
                        action="store")
    args = parser.parse_args()

    ns.org_id = args.i  # It's easier to make the user specify this than to grep  it from the token itself.
    ns.bearer = args.b  # We need a token as it's the cornerstone of the relevant security model.
    ns.debug = args.debug  # Even something this simple needs to be pulled.
    ns.path_output = args.o  # You could theoretically specify any relative or absolute path here. Most users won't.
    ns.use_eu = args.eu  # USDC and EUDC use different hosts.

    return ns


def process_to_csv(namespace):
    """We now have a full state object that contains all the user detail we
    need. All that remains is to create the output file.
    """
    ns = namespace
    if not ns.path_output:
        ns.path_output = str(date.today()) + ".csv"
    print("Passing file to %s" % ns.path_output)

    with open(ns.path_output, "w", encoding="utf-8") as output_file:
        fields = ["externalUserId", "id", "email", "isActive",
                  "loginName", "firstName", "lastName", "role", "updatedAt"]
        writer = csv.DictWriter(output_file, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()

        for each in ns.data_store:
            writer.writerow(each)

    return ns


def runtime():
    state = Namespace()
    display_welcome()
    state = parse_args(state)
    state = obtain_raw_json(state)
    state = process_to_csv(state)
    display_output(state)
    exit(0)


if __name__ == "__main__":
    runtime()
