-- I'd really like to make this apply only to those who take clawmachine_loans,
-- but this will have to do I guess. Note that setting this too low (eg 0.01)
-- seems to cap the number of loans drastically - not sure why. 0.02 is fine.
NDefines.NEconomy.MINIMUM_INTERESTS = 0.02

-- Hehe. This is a massive "player nations win" button, not what I was going
-- for, but rather funny. The AI never seems to use barrages, which instantly
-- give the maximum number of breaches - what I really wanted was for a boom
-- to still be worth three breaches, but then to still be able to have more
-- breaches happen organically (including if they had happened prior to the
-- booming of the walls). Raising the max makes barrages INSANELY effective!
-- NDefines.NMilitary.MAX_BREACH = 30
