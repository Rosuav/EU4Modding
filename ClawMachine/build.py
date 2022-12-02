# Generate the event modifiers and the decision-tree event for the Claw Machine

# Ideally, these rewards should all be exciting and somewhat OP, if perhaps
# demanding on your playstyle (eg getting a Build Time bonus will mean you
# benefit by spamming buildings). They should be very VERY roughly balanced
# against each other. It's fine to have different numbers of rewards in the
# categories, but no reward should feel truly disappointing, and no category
# should feel unexciting or overly predictable.

# Map something to None if its corresponding modifier has been manually
# created in 00_clawmachine.txt, or to a number to automatically create the
# modifier in 01_clawmachine_effects.txt. To create a province modifier, set
# to a list containing the value instead, eg [10], and the effect will be
# applied to the country's capital.

# NOTE: Currently, the "back out" option doesn't truly reroll; it instead
# wastes some RNG state on the subsequent attempts, thus showing new numbers
# to the user. According to the wiki, the "correct" way to rerandomize is to
# use an on_action or province trigger to disconnect the event chain. Which
# seems odd, since this isn't actually an event chain, and also doesn't seem
# to work properly. So we use this odd technique instead.
# Also - looping is rather verbose when you have nothing but a while loop.

EVENT_TEMPLATE = """# Autogenerated by build.py - do not edit
namespace = clawmachine

country_event = {
	id = clawmachine.1
	title = clawmachine.1.t
	desc = clawmachine.1.d
	picture = event_test
	is_triggered_only = yes
	immediate = {
		# Metaprogramming in EU4 is extremely limited. We can't set a string variable and then
		# say "add country modifier with this name", so we have a bunch of individual flags,
		# and have a corresponding switch block in the selection. The important thing is: the
		# randomness occurs here in the immediate block, allowing the player to make a decision
		# and be guaranteed to get the exact effect listed.
		hidden_effect = {
			change_variable = { which = claw_use_count value = 1 }
			# Skip the loop altogether on the first use, but after that, loop once per
			# additional use, thus affecting the random numbers used. The loop stops
			# when this counter is higher than the use count.
			set_variable = { which = claw_loop_count value = 2 }
			while = {
				limit = {
					check_variable = {
						which = claw_use_count
						which = claw_loop_count
					}
				}
				change_variable = { which = claw_loop_count value = 1 }
				# Waste four random numbers, thus advancing the PRNG and giving different
				# results in the all-important list selection below. This flag will never
				# be checked anywhere (and will almost always be true if the reset option
				# is used, but false if it wasn't).
				random = { chance = 50 set_country_flag = clawmachine_rng_flag }
				random = { chance = 50 set_country_flag = clawmachine_rng_flag }
				random = { chance = 50 set_country_flag = clawmachine_rng_flag }
				random = { chance = 50 set_country_flag = clawmachine_rng_flag }
			}
			# Random lists below are autogenerated to have equal weights (currently)%>%
			random_list = { # %sec%
%^%				1 = { set_country_flag = clawmachine_%opt% }
			}%<%
		}
	}%>%
	option = {
		name = clawmachine.1.%sec%
		trigger_switch = {
			on_trigger = has_country_flag
%^%			clawmachine_%opt% = { add_country_modifier = { name = clawmachine_%opt% duration = -1 } } #g
%^%			clawmachine_%opt% = { capital_scope = { add_permanent_province_modifier = { name = clawmachine_%opt% duration = -1 } } } #l
		}
	}%<%
	option = {
		name = clawmachine.1.abort
		add_prestige = -10
		hidden_effect = {
			country_event = {
				id = clawmachine.2
				days = 30
			}
		}
		custom_tooltip = "clawmachine.1.abortdesc"
		ai_chance = { factor = 100 }
	}
	after = {%>%
%^%		clr_country_flag = clawmachine_%opt%
%<%	}
}

# Delayed event to reenable the decision. This discourages frivolous rerolling, while still
# permitting it if none of the options suit the country in question.
country_event = {
	id = clawmachine.2
	title = clawmachine.1.t # Irrelevant since it's hidden
	desc = clawmachine.1.d
	picture = event_test
	is_triggered_only = yes
	hidden = yes
	immediate = {
		hidden_effect = {
			clr_country_flag = claw_machine_used
		}
	}
	option = { name = clawmachine.1.abort }
}
"""

rewards = {
	"sword": { # Military bonuses
		"ae_impact": -0.5,
		"siege_blockade_progress": 2, # No limit known. A blockaded siege becomes crazy fast at 10.
		"fort_maintenance_modifier": -1, # Capped at 90%?
		"recover_army_morale_speed": 0.5, # Recover X% of max morale each month
		"movement_speed": 2.5, # Cap? No idea.
		"global_regiment_recruit_speed": -1, # Seems to cap out at -0.8 after all modifiers, so this gives a little wiggle room
		"global_ship_recruit_speed": -1, # Ditto
		"defensiveness": 2, # Probably no cap. A value of 10 makes enemy sieges take most of a year per phase. That even applies to non-forts.
		"transport_attrition": -1, # 1.34 only. Removes attrition from troops on ships (though the ships themselves can still lose sailors).
		"military_tactics": 1, # 1.34 only. The tooltip says it's a percentage, but it seems to function as a hard number.
		"discipline": 0.25, # Most bonuses give 0.05, so this is five bonuses (eg Strict + Commandant + three others)
		"can_bypass_forts": "yes", # Ignore zone of control
		"leaders": None,
	},
	"coin": { # Financial bonuses
		"merchants": None, # Random names don't work properly if you apply this in a run file.
		"placed_merchant_power": 500, # No cap; is relative to the total trade power in the node, so this could be crazy big or fairly insignificant
		"ship_power_propagation": 2,
		"caravan_power": 9,
		"center_of_trade_upgrade_cost": -0.75,
		"great_project_upgrade_cost": -0.75,
		"inflation_action_cost": -1, # Effect caps at 90%
		"buildings": None,
		"global_prosperity_growth": 1, # Effectively doubles the rate at which prosperity grows, under its normal conditions. Underwhelming.
		"global_trade_goods_size": 1, # 1.34 only. Not a percentage; setting this to 1 is like having a manufactory everywhere.
	},
	"heart": { # Cultural bonuses and internal affairs
		"min_autonomy_in_territories": -0.5,
		"tolerance": None,
		"administrative_efficiency": 0.25, # Effects capped at 90%. Even 50% is kinda broken.
		"free_policy": 2,
		"governing_cost": -0.25, # Caps at -0.99.
		"monthly_reform_progress": 1, # Default is 0.83/month if you have no autonomy
		"culture_conversion_cost": -0.5, # Effects capped at 90% after this and all other modifiers.
		"num_accepted_cultures": 4,
		"no_stability_loss_on_monarch_death": "yes", # Can be achieved with some government reforms too, so this is a bit underwhelming
		"estates": None,
	},
	"globe": { # Discovery and diplomacy
		"improve_relation_modifier": 1,
		"prestige_decay": -0.02,
		"envoy_travel_time": -0.75,
		"range": 1,
		"native_assimilation": 10, # Has to be kinda crazy high to be really significant, but at 1000% it can make your colonies quite wealthy
		"innovativeness_gain": 1,
		"institution_growth": [120],
	},
}

import sys, os
root = os.path.dirname(sys.argv[0]) or "."
# Note that only the English localisation will be autogenerated. If this mod ever gets
# other translations done, they'll need to be thought about separately.
with open(root + "/common/event_modifiers/01_clawmachine_effects.txt", "w") as eff, open(root + "/localisation/clawmachine_effects_l_english.yml", "w") as loc:
	print("# Autogenerated from build.py - do not edit", file=eff)
	print("\ufeffl_english:", file=loc)
	for sec, opts in rewards.items():
		for n, (id, val) in enumerate(opts.items(), 1):
			#print(' clawmachine_%s:0 "Cosmic Claw Machine %s:%d"' % (id, sec[0].upper(), n), file=loc) # For debugging, distinguish all the modifier names
			print(' clawmachine_%s:0 "Cosmic Claw Machine"' % id, file=loc)
			if isinstance(val, list): val = val[0] # Country vs capital scope is handled elsewhere
			if val is None: continue
			print("clawmachine_%s = {" % id, file=eff)
			print("\t%s = %s" % (id, val), file=eff)
			print("}", file=eff)

# The event template has some markers in it.
# "%>% ... %<%": This block is repeated once for each section. Use %sec% for the section keyword.
# "%^% ... \n": This line is repeated once for each option. Use %opt% for the effect ID.

with open(root + "/events/clawmachine.txt", "w") as evfile:
	evt = EVENT_TEMPLATE
	while evt:
		before, part, after = evt.partition("%>%")
		evfile.write(before)
		if part:
			section, part, after = after.partition("%<%")
			if not part:
				print("ERROR IN TEMPLATE: Mismatched markers")
				break # File will be incomplete at the point of the broken marker
			for sec, opts in rewards.items():
				text = section.replace("%sec%", sec)
				while text:
					b, _, a = text.partition("%^%")
					evfile.write(b)
					o, p, a = a.partition("\n")
					if p:
						for id, val in opts.items():
							# Filtered 
							if o.endswith("#g") and isinstance(val, list): continue
							if o.endswith("#l") and not isinstance(val, list): continue
							evfile.write(o.replace("%opt%", id) + p)
					text = a
		evt = after
