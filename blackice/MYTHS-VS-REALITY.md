# Myths versus reality

Security specialists need to tell the real from the fiction, and the fiction here is thick. Cyberpunk stories, vendor marketing and a lot of forum talk blur "defending hard" into "hitting back." This page separates them.

This is general orientation, not legal advice. Laws differ by country and change. Have counsel read anything you plan to ship, and treat the court and agency examples below as publicly reported, to be checked before you cite them.

| Myth | Reality | What Black ICE does instead |
| --- | --- | --- |
| "If they hack me first, I may hack back." | In most places, no. Accessing a computer without authorization is an offense whoever started it. In the US that is the Computer Fraud and Abuse Act. The UK's Computer Misuse Act and most European national laws work the same way. Bills to allow limited hack-back have been proposed, and as far as I know none became law in the US. Check the current position. | Contain, deceive and record on your own systems. |
| "I can counterstrike the address that attacked me." | Attribution is weak. Bots usually run from hijacked machines, such as a small clinic's server, so a counterstrike lands on a victim. | Report the address to its host, with evidence. |
| "Automatic retaliation is safe because it is only reacting." | An automatic response can be triggered by a forged signal. An attacker can make your system hit a third party of their choosing. That is a confused-deputy attack, the same family the range measures in ASI03. | No retaliation rung. Containment acts on your own assets only, and needs corroboration. |
| "Honeypots are entrapment." | Entrapment is a defense for people induced by government agents to commit a crime. A passive honeypot on your own systems is widely used and generally not that. The risks are different: a decoy that can reach out harms third parties, and a decoy that real users find gives them wrong answers. Have counsel confirm for your country. | Sealed decoys with no outbound path, away from real use. |
| "Bait that phones home from the attacker's machine is fine." | It runs code on their system, which is the same line as hacking back, and in some places a legal gray area at best. | Server-side observation only: what reaches your gateway. |
| "Taking down a botnet is a job for a vigilante." | Legitimate takedowns run through courts and agencies. Microsoft's Digital Crimes Unit has used civil court orders to seize domains. The FBI has used warrants to remove malware from victims' servers, as publicly reported for the 2021 Exchange web shells. A company acting alone has no such cover. | Report, and cooperate with those who have the authority. |
| "Reporting is useless." | Often the opposite. Telling the issuer of a stolen token lets it revoke the token everywhere, which stops every thief at once. | Scribe drafts the report, a person sends it. |
| "Real ICE can fry the attacker's brain." | That is Gibson. Nothing real works that way, and nothing like it would be legal or wise. | Slow, mislead, contain and document. |
| "Active defense means offense." | The term is used loosely. Deception, tarpits and containment on your own systems are defense even though they act. Reaching into someone else's systems is offense however it is labeled. Vendors blur this. | Rungs one to four only. |
| "Threat intel is facts." | It is data from parties who may be wrong or hostile. A feed that auto-blocks addresses can be turned against your own users with a forged source. | Intel is data, not orders. No action on one unverified signal. |
| "More automation is more protection." | Every agent that can quarantine or block is another thing an attacker can hijack or impersonate, and the cheapest attack on an automatic defense is to trigger it against its owner. | Small powers, human sign-off on anything irreversible, and the crew tested as a target. |

## Why this page exists

The project's rule is to claim only what a saved run supports, and to say plainly where a popular idea is wrong. Hack-back is the clearest case in this field of an idea that sounds like strength and fails on law, on attribution and on forgeability. A defense that knows where the line is can be strong inside it.
