# Generate the decision and localisation files from the core buildings files
# Note that this ignores all mods and operates directly on the base files.
import json
import os.path
import re
import subprocess
import sys
from collections import defaultdict
# Is there a way to ask Steam where the game's installed? No biggie, it's just for
# updating after a big game change.
GAME_DIR = os.path.expanduser("~/.steam/steam/steamapps/common/Europa Universalis IV")
# See the EU4Parse repository, which has a yacc-based parser. Use what already exists, eh?
PARSER = os.path.expanduser("~/EU4Parse/savefile")
BUILDINGS_DIR = GAME_DIR + "/common/buildings"
L10N_DIR = GAME_DIR + "/localisation"

# Hackily parse the localisation files and try to find the names.
# TODO: Don't do this at all; reference the keys in question instead of copying the values.
names = { }
for fn in sorted(os.listdir(L10N_DIR)):
	if not fn.endswith("english.yml"): continue
	with open(L10N_DIR + "/" + fn, "rt") as f:
		next(f) # Skip the heading
		for line in f:
			if m := re.match(r"^ building_(.*?):[0-9]+ \"(.*?)\"$", line):
				names[m.group(1)] = m.group(2)

def L10N(id): return names.get(id, id)

# First figure out the full list of buildings that obsolete other buildings.
# If anything fails at this stage (eg parsing the files), don't destroy the script file.
obsoletes = { }; requires_port = { }; obsoleted_by = { }
prices = defaultdict(int)
for fn in sorted(os.listdir(BUILDINGS_DIR)):
	p = subprocess.run([PARSER, BUILDINGS_DIR + "/" + fn], capture_output=True)
	data = json.loads(p.stdout)
	for id, info in data.items():
		if "allowed_num_of_buildings" in info.get("modifier", {}):
			# Courthouse, Town Hall, and University don't require a building slot.
			# We can "upgrade" them from nothing, and it still won't consume a slot.
			if "manufactory" in info:
				# However, the State House, while it doesn't consume a building slot,
				# *does* consume a manufactory slot. As such, it's not the no-brainer
				# build whenever you have money, and doesn't belong in this tool.
				# Maybe it should? Not sure. (Note that this code would crash if it
				# were to be enabled, as the cost is inherited from the generic
				# "manufactory" block; that's easily fixed but for now unnecessary.)
				continue
			obsoletes[id] = ()
			prices[(), id] = int(info["cost"])
			if prev := info.get("make_obsolete"):
				obsoleted_by[prev] = id
			print("%20s []" % L10N(id))
			continue
		if "manufactory" not in info and id != "manufactory":
			requires_port[id] = "has_port" in info.get("build_trigger", {})
		if "cost" in info: prices[(), id] = int(info["cost"])
		if "make_obsolete" not in info: continue
		obsoletes[id] = [*obsoletes.get(info["make_obsolete"], ()), info["make_obsolete"]]
		obsoleted_by[info["make_obsolete"]] = id
		for old in obsoletes[id]:
			prices[old, id] = int(info["cost"]) - int(data[old]["cost"])
		print("%20s %r" % (L10N(id), obsoletes[id]))

# For convenience, add entries into obsoletes for all the base buildings too.
for id in requires_port:
	if id not in obsoletes: obsoletes[id] = "decision-only"

UPGRADE = """	upgrade_to_$new$ = {
		color = { 102 51 153 } # rebeccapurple
		potential = {
			# This SHOULD be balanced, but for now, make it player-only
			ai = no
			any_owned_province = {
				can_build = $new$$replaced$
				$has$
			}
		}
		allow = {
			any_owned_province = {
				can_build = $new$$replaced$
				$has$
			}
			treasury = $price$ # Note that this ignores cost modifications. You have to have the base price on hand.
		}
		effect = {
			custom_tooltip = upgrade_to_$new$_tt
			hidden_effect = {
				every_owned_province = {
					limit = {
						can_build = $new$$replaced$
						$has$
						owner = { treasury = $price$ } # Once you no longer have the base price, stop building.
					}
					add_building_construction = { building = $new$ }
					save_event_target_as = last_built_province
				}
				# If it took you into the red...
				if = {
					limit = { NOT = { treasury = 0 } }
					# ... cancel the last one built.
					# This isn't perfect - I would much rather the number in both "allow" and "limit" were
					# affected by actual cost modifications - but at least you won't go into debt for this.
					event_target:last_built_province = { cancel_construction = yes }
				}
			}
		}
		ai_will_do = {
			factor = 0
		}
	}
"""

CELEBRATE = """	celebrate_$id$ = {
		color = { 102 51 153 } # rebeccapurple
		potential = {
			ai = no
			has_country_flag = guide_infra_$id$
		}
		allow = {
			custom_trigger_tooltip = {
				tooltip = celebrate_allow
				always = yes
			}
		}
		provinces_to_highlight = {
			owned_by = ROOT
			NOT = { has_building = $id$ }
			$has_port$
		}
		effect = {
			custom_tooltip = celebrate_effect
			clr_country_flag = guide_infra_$id$
			country_event = { id = bulkupgrades.2 }
		}
		ai_will_do = {
			factor = 0
		}
	}
"""

EVENT = """namespace = bulkupgrades
country_event = {
	id = bulkupgrades.1
	title = bulkupgrades.1.t
	desc = bulkupgrades.1.d
	picture = CITY_DEVELOPMENT_eventPicture
	is_triggered_only = yes
	immediate = {
$imm$	}$opt$
	option = {
		name = bulkupgrades.1.none
	}
}
country_event = {
	id = bulkupgrades.2
	title = bulkupgrades.2.t
	desc = bulkupgrades.2.d
	picture = CITY_DEVELOPMENT_eventPicture
	is_triggered_only = yes
	option = {
		name = bulkupgrades.2.ok
	}
}
country_event = {
	id = bulkupgrades.3
	title = bulkupgrades.3.t
	desc = bulkupgrades.3.d
	picture = COLONIZATION_eventPicture
	is_triggered_only = yes
	option = {
		name = bulkupgrades.3.ok
	}
}
"""

TOP_MATTER = """# AUTOGENERATED BY build.py - DO NOT EDIT
country_decisions = {
	# This is pushing the definition of 'upgrade' a bit, but if you have the ability
	# to establish Siberian Frontiers, you can... upgrade uncolonized provinces to
	# frontiers?? This doesn't actually do the upgrade though, it only points it out.
	upgrade_province_to_frontier = {
		color = { 32 128 32 }
		potential = {
			ai = no
			# Note that this looks really ugly in the hover text (you have to
			# have at least +100% May Establish Siberian Frontiers), but it's
			# best in the Potential section anyway - if you don't have the
			# ability, the decision isn't very relevant.
			has_global_modifier_value = {
				which = may_establish_frontier
				value = 1
			}
		}
		allow = {
			any_owned_province = {
				is_city = yes
				is_in_capital_area = yes
				has_empty_adjacent_province = yes
			}
			# Is there any way to trigger on "can pay this price"? If you have discounts,
			# the decision won't trigger till you have the full 20 - not that it makes a
			# LOT of difference, but still.
			dip_power = 20
		}
		provinces_to_highlight = {
			owned_by = ROOT
			is_city = yes
			is_in_capital_area = yes
			has_empty_adjacent_province = yes
		}
		effect = {
			custom_tooltip = upgrade_province_to_frontier_effect
			country_event = { id = bulkupgrades.3 }
		}
	}"""

# NOTE: This text is not allowed to contain double quotes, as we cheat and use !r to make a quoted string out of it.
BULKUPGRADES_DESC = """
Sire, our infrastructure could be expanded in any number of directions. What should we be focusing on?

§PUse this when you wish to §Jdevelop§! provinces in order to build more of a building.§!

When you select a building type, we will locate places it can be built. Then it's up to you to ready them for construction!

§PSelecting a building type will enable a second decision. Use that decision's '§JClick to Center§!' button to find the provinces which can be developed to add this building.§!

As much or as little as you need, we will build.

§PThe secondary decision will remove itself and allow you to reselect this one. Recommendation: Disable §Jnotification status§! on this decision.§!
"""
BULKUPGRADES_DONE_DESC = """
We're done! For now. If you wish to guide our infrastructure expansion in a different direction, we will be happy to assist.

§PRecommendation: Disable §Jnotification status§! on the main infrastructure upgrade decision.§!
"""
FRONTIER_DESC = """
Lands are opening up and our people are eager to seek new opportunities!

§PThis decision will help you find cities near potential Frontiers. Use the '§JClick to Center§!' button to jump to one such city, then establish a Frontier near it.§!

Send out our colonizers and take this land for our glorious nation!
"""

root = os.path.dirname(sys.argv[0]) or "."
with open("decisions/00_bulk_upgrades.txt", "wt") as f, open("localisation/bulkupgrades_l_english.yml", "wt") as loc, open("events/00_bulk_upgrades.txt", "wt") as evt:
	print(TOP_MATTER, file=f)
	print(f"""\ufeffl_english:
 celebrate_desc:0 "Once you're satisfied with your building construction, you can deem it done."
 celebrate_allow:0 "The power of this decision is right here in your hands - to find a province to develop, click to center!"
 celebrate_effect:0 "Feel good about your building construction"
 guide_infra_expansion_title:0 "Guide expansion of infrastructure"
 guide_infra_expansion_desc:0 "Select a building type to try to add more of"
 is_expanding_infrastructure_tooltip:0 "Currently seeking expansion of this building type"
 upgrade_province_to_frontier_title:0 "Upgrade province frontiers"
 upgrade_province_to_frontier_desc:0 "Pinpoint provinces with room to expand their frontiers"
 upgrade_province_to_frontier_effect:0 "Learn more about this decision"
 bulkupgrades.1.t:0 "Guide expansion of infrastructure"
 bulkupgrades.1.d:0 {BULKUPGRADES_DESC.strip()!r}
 bulkupgrades.1.none:0 "There's nothing we need that desperately right now."
 bulkupgrades.2.t:0 "Infrastructure expansion complete"
 bulkupgrades.2.d:0 {BULKUPGRADES_DONE_DESC.strip()!r}
 bulkupgrades.2.ok:0 "Well done."
 bulkupgrades.3.t:0 "Frontier Expansion"
 bulkupgrades.3.d:0 {FRONTIER_DESC.strip()!r}
 bulkupgrades.3.ok:0 "Will do!"\
""", file=loc)
	for new, olds in obsoletes.items():
		if not olds:
			has = "" # No requirement to have a previous building
		elif olds == "decision-only":
			# No previous building, so this is only available when expanding infrastructure.
			has = "is_expanding_infrastructure = { BUILDING = " + new + " }"
			olds = ()
		else:
			# Has to have the previous building, or you're expanding infrastructure
			has = "OR = { is_expanding_infrastructure = { BUILDING = " + new + " }" + "".join(" has_building = " + id for id in olds) + " }"
		if replacement := obsoleted_by.get(new):
			# Once you're able to build Stock Exchanges, stop offering the decision to
			# build Trade Depots (since the Stock Exchanges decision will now be open).
			replaced = " NOT = { can_build = " + replacement + " }"
		else: replaced = ""
		# TODO: Change the hover text to be descriptive rather than exhaustive
		print(UPGRADE
			.replace("$new$", new)
			.replace("$has$", has)
			.replace("$replaced$", replaced)
			# TODO: Check treasury based on *each* possible upgrade, not a single price for all
			.replace("$price$", str(prices[olds and olds[0], new]))
		, file=f)
		print(' upgrade_to_%s_title:0 "Building upgrade: %s"' % (new, L10N(new)), file=loc)
		print(' upgrade_to_%s_desc:0 "Start upgrading as many as you can afford to %s"' % (new, L10N(new)), file=loc)
		print(' upgrade_to_%s_tt:0 "Start construction of a §Y%s§! in every province that has %s"' % (
			new, L10N(new),
			" or ".join("§Y%s§!" % L10N(o) for o in olds) if olds else "none" # "that has none" reads okayish
		), file=loc)
	imm = opt = ""
	for id, need_port in requires_port.items():
		print(CELEBRATE
			.replace("$id$", id)
			.replace("$has_port$", "has_port = yes" if need_port else "# inland, no port needed")
		, file=f)
		print(' celebrate_%s_title:0 "Celebrate your %s construction"' % (id, L10N(id)), file=loc)
		imm += "		clr_country_flag = guide_infra_" + id + "\n"
		opt += """
	option = {
		trigger = { ROOT = { $id$ = 1 } }
		name = building_$id$
		set_country_flag = guide_infra_$id$
	}""".replace("$id$", id)
	print(EVENT.replace("$imm$", imm).replace("$opt$", opt), file=evt)
	print("""	guide_infra_expansion = {
		color = { 102 51 153 } # rebeccapurple
		potential = { ai = no }
		allow = { always = yes }
		effect = {
			country_event = { id = bulkupgrades.1 }
		}
	}
}""", file=f)
