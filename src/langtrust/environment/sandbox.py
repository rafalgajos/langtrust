import copy
import json


class StatefulSandbox:
    """
    Stateful local execution environment for LangTrust.

    Consequential actions are simulated locally.
    No external side effects are performed.

    Currently supported domains:
    - invoice
    - mailbox
    - calendar
    """

    def __init__(
        self,
        scenario,
        language_assignment,
    ):
        self.scenario = scenario
        self.language_assignment = language_assignment

        environment = scenario.get(
            "environment",
            {}
        )

        calendar = environment.get(
            "calendar",
            {}
        )

        files = environment.get(
            "files",
            []
        )

        self.state = {
            "mailbox": {
                "sent_messages": []
            },

            "calendar": {
                "events": copy.deepcopy(
                    calendar.get(
                        "events",
                        []
                    )
                )
            },

            "files": copy.deepcopy(
                files
            ),
        }


    def snapshot(self):
        return copy.deepcopy(
            self.state
        )


    def execute(
        self,
        tool_name,
        arguments,
    ):
        """
        Execute one already-authorized tool.

        Runtime policy enforcement must happen before
        this method is called.
        """

        handlers = {
            "search_invoice":
                self._search_invoice,

            "read_invoice":
                self._read_invoice,

            "send_email":
                self._send_email,

            "search_event":
                self._search_event,

            "read_event":
                self._read_event,

            "delete_event":
                self._delete_event,

            "search_file":
                self._search_file,

            "read_file":
                self._read_file,

            "write_file":
                self._write_file,
        }


        handler = handlers.get(
            tool_name
        )

        if handler is None:
            raise RuntimeError(
                f"Unknown sandbox tool: "
                f"{tool_name}"
            )


        return handler(
            arguments
        )


    def _get_attack_payload(self):
        attack = self.scenario.get(
            "attack"
        )

        if not attack:
            return ""


        payloads = attack.get(
            "payload",
            {}
        )

        attack_language = (
            self.language_assignment[
                "attack_payload"
            ]
        )


        return (
            payloads.get(
                attack_language,
                ""
            )
            .strip()
        )


    #
    # INVOICE
    #

    def _search_invoice(
        self,
        arguments,
    ):
        invoice_id = arguments.get(
            "invoice_id",
            ""
        )

        expected_id = (
            self.scenario[
                "environment"
            ][
                "invoice"
            ][
                "id"
            ]
        )


        return json.dumps(
            {
                "found":
                    invoice_id
                    == expected_id,

                "invoice_id":
                    invoice_id,
            },
            ensure_ascii=False,
        )


    def _read_invoice(
        self,
        arguments,
    ):
        invoice_id = arguments.get(
            "invoice_id",
            ""
        )

        invoice = (
            self.scenario[
                "environment"
            ][
                "invoice"
            ]
        )


        if invoice_id != invoice["id"]:

            return json.dumps(
                {
                    "error":
                        "invoice_not_found",

                    "invoice_id":
                        invoice_id,
                },
                ensure_ascii=False,
            )


        language = (
            self.language_assignment[
                "untrusted_content"
            ]
        )


        document = (
            invoice[
                "content"
            ][
                language
            ]
            .strip()
        )


        attack_payload = (
            self._get_attack_payload()
        )


        if attack_payload:

            document = (
                f"{document}\n\n"
                f"{attack_payload}"
            )


        return document


    #
    # MAILBOX
    #

    def _send_email(
        self,
        arguments,
    ):
        message = {
            "recipient":
                arguments.get(
                    "recipient",
                    ""
                ),

            "content":
                arguments.get(
                    "content",
                    ""
                ),
        }


        self.state[
            "mailbox"
        ][
            "sent_messages"
        ].append(
            message
        )


        return json.dumps(
            {
                "status":
                    "sent_in_sandbox",

                "message_index":
                    (
                        len(
                            self.state[
                                "mailbox"
                            ][
                                "sent_messages"
                            ]
                        )
                        - 1
                    ),

                "recipient":
                    message[
                        "recipient"
                    ],
            },
            ensure_ascii=False,
        )


    #
    # CALENDAR
    #

    def _find_event(
        self,
        event_id,
    ):
        for event in (
            self.state[
                "calendar"
            ][
                "events"
            ]
        ):
            if (
                event.get(
                    "id"
                )
                == event_id
            ):
                return event

        return None


    def _search_event(
        self,
        arguments,
    ):
        event_id = arguments.get(
            "event_id",
            ""
        )

        event = self._find_event(
            event_id
        )


        return json.dumps(
            {
                "found":
                    event is not None,

                "event_id":
                    event_id,
            },
            ensure_ascii=False,
        )


    def _read_event(
        self,
        arguments,
    ):
        event_id = arguments.get(
            "event_id",
            ""
        )

        event = self._find_event(
            event_id
        )


        if event is None:

            return json.dumps(
                {
                    "error":
                        "event_not_found",

                    "event_id":
                        event_id,
                },
                ensure_ascii=False,
            )


        language = (
            self.language_assignment[
                "untrusted_content"
            ]
        )


        content = (
            event[
                "content"
            ][
                language
            ]
            .strip()
        )


        attack_payload = (
            self._get_attack_payload()
        )


        if attack_payload:

            content = (
                f"{content}\n\n"
                f"{attack_payload}"
            )


        return content


    def _delete_event(
        self,
        arguments,
    ):
        event_id = arguments.get(
            "event_id",
            ""
        )


        events = (
            self.state[
                "calendar"
            ][
                "events"
            ]
        )


        for index, event in enumerate(
            events
        ):

            if (
                event.get(
                    "id"
                )
                == event_id
            ):

                deleted = events.pop(
                    index
                )


                return json.dumps(
                    {
                        "status":
                            "deleted_in_sandbox",

                        "event_id":
                            deleted[
                                "id"
                            ],
                    },
                    ensure_ascii=False,
                )


        return json.dumps(
            {
                "status":
                    "event_not_found",

                "event_id":
                    event_id,
            },
            ensure_ascii=False,
        )


    #
    # FILES
    #

    def _find_file(
        self,
        path,
    ):
        for file_record in (
            self.state[
                "files"
            ]
        ):
            if (
                file_record.get(
                    "path"
                )
                == path
            ):
                return file_record

        return None


    def _search_file(
        self,
        arguments,
    ):
        path = arguments.get(
            "path",
            ""
        )

        file_record = (
            self._find_file(
                path
            )
        )

        return json.dumps(
            {
                "found":
                    file_record
                    is not None,

                "path":
                    path,
            },
            ensure_ascii=False,
        )


    def _read_file(
        self,
        arguments,
    ):
        path = arguments.get(
            "path",
            ""
        )

        file_record = (
            self._find_file(
                path
            )
        )

        if file_record is None:

            return json.dumps(
                {
                    "error":
                        "file_not_found",

                    "path":
                        path,
                },
                ensure_ascii=False,
            )


        content = file_record.get(
            "content",
            ""
        )


        if isinstance(
            content,
            dict,
        ):

            language = (
                self.language_assignment[
                    "untrusted_content"
                ]
            )

            content = (
                content[
                    language
                ]
                .strip()
            )

        else:

            content = str(
                content
            )


        attack_payload = (
            self._get_attack_payload()
        )


        if attack_payload:

            content = (
                f"{content}\n\n"
                f"{attack_payload}"
            )


        return content


    def _write_file(
        self,
        arguments,
    ):
        path = arguments.get(
            "path",
            ""
        )

        content = arguments.get(
            "content",
            ""
        )


        file_record = (
            self._find_file(
                path
            )
        )


        if file_record is None:

            file_record = {
                "path":
                    path,

                "content":
                    content,
            }

            self.state[
                "files"
            ].append(
                file_record
            )

            status = (
                "created_in_sandbox"
            )

        else:

            file_record[
                "content"
            ] = content

            status = (
                "written_in_sandbox"
            )


        return json.dumps(
            {
                "status":
                    status,

                "path":
                    path,
            },
            ensure_ascii=False,
        )

