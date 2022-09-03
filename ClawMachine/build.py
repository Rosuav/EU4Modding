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

# Goal: When the event fires, randomly pick four event options. (See eg the
# "muslim_school_events.2" event, which has individual chances of bad/ok/good
# for each of its options.) The player will be presented with four options,
# and while it's possible that one of them might be inapplicable, it's highly
# unlikely that all four will be useless. NOTE: Since it will rerandomize on
# cancel/repick, there needs to be a cooldown or cost on that last option.
rewards = {
	"sword": { # Military bonuses
# ae_impact
# siege_blockade_progress
		"fort_maintenance_modifier": -1,
# recover_army_morale_speed
# movement_speed
# global_regiment_recruit_speed
# global_ship_recruit_speed
# defensiveness
	},
	"coin": { # Financial bonuses
# merchants
		"placed_merchant_power": 500,
# ship_power_propagation
# caravan_power
# center_of_trade_upgrade_cost
# great_project_upgrade_cost
# inflation_action_cost
# build_time
# global_prosperity_growth
	},
	"heart": { # Cultural bonuses and internal affairs
# min_autonomy_in_territories
		"tolerance": None,
# administrative_efficiency
# possible_policy
# governing_cost
# monthly_reform_progress
# culture_conversion_cost
# num_accepted_cultures
		# "all_estate_loyalty_equilibrium": 1,
	},
	"globe": { # Discovery and diplomacy
# improve_relation_modifier
# prestige_decay
# envoy_travel_time
# range = 1.0 (colonial range - this should be a 100% bonus)
# native_assimilation
# innovativeness_gain
		"institution_growth": [120],
	},
}

import sys, os
root = os.path.dirname(sys.argv[0])
# Note that only the English localisation will be autogenerated. If this mod ever gets
# other translations done, they'll need to be thought about separately.
with open(root + "/common/event_modifiers/01_clawmachine_effects.txt", "w") as eff, open(root + "/localisation/clawmachine_effects_l_english.yml", "w") as loc:
	print("# Autogenerated from build.py - do not edit", file=eff)
	print("\ufeffl_english:", file=loc)
	for sec, opts in rewards.items():
		for id, val in opts.items():
			print(' clawmachine_%s:0 "Cosmic Claw Machine"' % id, file=loc)
			# TODO: Generate event option randomization too
			if isinstance(val, list):
				# Create a capital_scope effect
				val = val[0]
			# else: # Normally just add_country_modifier
			if val is None: continue
			print("clawmachine_%s = {" % id, file=eff)
			print("\t%s = %s" % (id, val), file=eff)
			print("}", file=eff)
