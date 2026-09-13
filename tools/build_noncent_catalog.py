#!/usr/bin/env python3
"""Build broad, source-dated screening rules for U.S. 5c through $1 coins."""
import json
from pathlib import Path

OUT=Path(__file__).resolve().parents[1]/"catalog"/"us_noncent.json"
DATE="2026-09-13"
PCGS="https://www.pcgs.com/prices/us"

def prices(g,f,vf,xf,au,ms):
    return {"G":g,"F":f,"VF":vf,"XF":xf,"AU":au,"MS":ms}

def rule(denom,start,end,series,mints,p,composition,weight,diameter,excluded=None):
    return {"country":"USA","denomination":denom,"year_start":start,"year_end":end,
            "series":series,"mint_marks":mints,"composition":composition,"weight_g":weight,
            "diameter_mm":diameter,"source_url":PCGS,"price_source":"CoinScope conservative range informed by PCGS Price Guide",
            "price_updated":DATE,"prices":p,"excluded_years":excluded or []}

R=[]
# Five cents
R += [
 rule("5c",1866,1883,"Shield Nickel",[""],prices([20,35],[30,55],[50,90],[85,150],[140,300],[350,2500]),"75% copper, 25% nickel",5.0,20.5),
 rule("5c",1883,1912,"Liberty Head V Nickel",["","D","S"],prices([3,8],[6,15],[12,30],[25,65],[60,150],[175,1200]),"75% copper, 25% nickel",5.0,21.2),
 rule("5c",1913,1938,"Buffalo Nickel",["","D","S"],prices([1,4],[2,8],[5,20],[15,45],[35,120],[100,1200]),"75% copper, 25% nickel",5.0,21.2),
 rule("5c",1938,1942,"Jefferson Nickel",["","D","S"],prices([0.05,0.20],[0.05,0.30],[0.10,0.50],[0.20,1],[0.50,3],[2,50]),"75% copper, 25% nickel",5.0,21.2),
 rule("5c",1942,1945,"Jefferson Wartime Silver Nickel",["P","S"],prices([3,5],[3,6],[3,7],[4,9],[6,15],[12,150]),"56% copper, 35% silver, 9% manganese",5.0,21.2),
 rule("5c",1946,2026,"Jefferson Nickel",["","P","D","S"],prices([0.05,0.20],[0.05,0.30],[0.10,0.50],[0.20,1],[0.50,3],[2,50]),"75% copper, 25% nickel",5.0,21.2),
]
# Dimes
R += [
 rule("10c",1850,1891,"Liberty Seated Dime",["","O","S","CC"],prices([20,40],[30,65],[50,110],[90,180],[160,350],[400,3000]),"90% silver",2.49,17.9),
 rule("10c",1892,1916,"Barber Dime",["","D","O","S"],prices([5,12],[8,20],[15,40],[30,80],[70,180],[200,1500]),"90% silver",2.50,17.9),
 rule("10c",1916,1945,"Mercury Dime",["","D","S"],prices([5,10],[6,14],[8,22],[12,40],[25,100],[75,1000]),"90% silver",2.50,17.9),
 rule("10c",1946,1964,"Roosevelt Dime, Silver",["","D","S"],prices([5,8],[5,9],[5,10],[6,12],[8,20],[15,150]),"90% silver",2.50,17.9),
 rule("10c",1965,2026,"Roosevelt Dime, Clad",["","P","D","S","W"],prices([0.10,0.20],[0.10,0.25],[0.10,0.35],[0.10,0.50],[0.15,1],[1,30]),"Copper-nickel clad",2.268,17.9),
]
# Quarters
R += [
 rule("25c",1850,1891,"Liberty Seated Quarter",["","O","S","CC"],prices([35,75],[55,110],[90,180],[150,300],[275,650],[750,6000]),"90% silver",6.22,24.3),
 rule("25c",1892,1916,"Barber Quarter",["","D","O","S"],prices([25,50],[40,80],[70,140],[115,250],[225,500],[500,5000]),"90% silver",6.25,24.3),
 rule("25c",1916,1930,"Standing Liberty Quarter",["","D","S"],prices([25,60],[40,85],[70,150],[120,275],[250,600],[500,6000]),"90% silver",6.25,24.3,[1922]),
 rule("25c",1932,1964,"Washington Quarter, Silver",["","D","S"],prices([12,20],[12,22],[13,25],[15,35],[22,65],[35,500]),"90% silver",6.25,24.3,[1933]),
 rule("25c",1965,1998,"Washington Quarter, Clad",["","P","D","S"],prices([0.25,0.50],[0.25,0.75],[0.25,1],[0.40,2],[1,5],[3,100]),"Copper-nickel clad",5.67,24.3),
 rule("25c",1999,2008,"Washington State Quarter",["P","D","S"],prices([0.25,0.50],[0.25,0.75],[0.25,1],[0.50,2],[1,5],[3,50]),"Copper-nickel clad",5.67,24.3),
 rule("25c",2009,2009,"DC and Territories Quarter",["P","D","S"],prices([0.25,0.50],[0.25,0.75],[0.25,1],[0.50,2],[1,5],[3,50]),"Copper-nickel clad",5.67,24.3),
 rule("25c",2010,2021,"America the Beautiful Quarter",["P","D","S","W"],prices([0.25,0.50],[0.25,0.75],[0.25,1],[0.50,2],[1,5],[3,60]),"Copper-nickel clad",5.67,24.3),
 rule("25c",2022,2025,"American Women Quarter",["P","D","S"],prices([0.25,0.50],[0.25,0.75],[0.25,1],[0.50,2],[1,5],[3,40]),"Copper-nickel clad",5.67,24.3),
 rule("25c",2026,2026,"Semiquincentennial Quarter",["P","D","S"],prices([0.25,0.50],[0.25,0.75],[0.25,1],[0.50,2],[1,5],[3,50]),"Copper-nickel clad",5.67,24.3),
]
# Half dollars
R += [
 rule("50c",1850,1891,"Liberty Seated Half Dollar",["","O","S","CC"],prices([55,110],[85,160],[130,250],[225,450],[400,900],[1000,8000]),"90% silver",12.44,30.6),
 rule("50c",1892,1915,"Barber Half Dollar",["","D","O","S"],prices([30,60],[50,100],[85,170],[150,300],[275,650],[700,6000]),"90% silver",12.50,30.6),
 rule("50c",1916,1947,"Walking Liberty Half Dollar",["","D","S"],prices([25,50],[35,75],[60,130],[100,225],[200,500],[500,5000]),"90% silver",12.50,30.6),
 rule("50c",1948,1963,"Franklin Half Dollar",["","D","S"],prices([25,35],[25,40],[27,45],[30,60],[40,100],[75,1000]),"90% silver",12.50,30.6),
 rule("50c",1964,1964,"Kennedy Half Dollar, 90% Silver",["","D"],prices([25,35],[25,40],[27,45],[30,60],[40,100],[75,750]),"90% silver",12.50,30.6),
 rule("50c",1965,1970,"Kennedy Half Dollar, 40% Silver",["","D","S"],prices([10,18],[10,20],[12,22],[15,30],[20,45],[35,250]),"40% silver",11.50,30.6),
 rule("50c",1971,2026,"Kennedy Half Dollar, Clad",["","P","D","S"],prices([0.50,1],[0.50,1.25],[0.50,1.50],[0.75,3],[2,8],[5,100]),"Copper-nickel clad",11.34,30.6),
]
# Dollars
R += [
 rule("1 Dollar",1850,1873,"Liberty Seated Dollar",["","O","S","CC"],prices([300,550],[450,800],[700,1400],[1200,2500],[2200,5000],[6000,40000]),"90% silver",26.73,38.1),
 rule("1 Dollar",1873,1885,"Trade Dollar",["","S","CC"],prices([250,500],[400,750],[650,1200],[1000,1800],[1600,3000],[3000,25000]),"90% silver",27.22,38.1),
 rule("1 Dollar",1878,1921,"Morgan Dollar",["","D","O","S","CC"],prices([50,75],[55,90],[65,120],[85,180],[150,400],[300,5000]),"90% silver",26.73,38.1,list(range(1905,1921))),
 rule("1 Dollar",1921,1935,"Peace Dollar",["","D","S"],prices([45,70],[50,85],[60,110],[80,160],[140,350],[275,3000]),"90% silver",26.73,38.1,list(range(1929,1934))),
 rule("1 Dollar",1971,1978,"Eisenhower Dollar",["","D","S"],prices([1,3],[1,4],[1,5],[2,8],[5,20],[10,150]),"Copper-nickel clad; some S issues contain silver",22.68,38.1),
 rule("1 Dollar",1979,1999,"Susan B. Anthony Dollar",["P","D","S"],prices([1,2],[1,2],[1,3],[2,5],[3,10],[5,100]),"Copper-nickel clad",8.10,26.5,list(range(1982,1999))),
 rule("1 Dollar",2000,2008,"Sacagawea Dollar",["P","D","S"],prices([1,2],[1,2],[1,3],[2,5],[3,10],[5,100]),"Manganese-brass clad",8.10,26.5),
 rule("1 Dollar",2009,2026,"Native American Dollar",["P","D","S"],prices([1,2],[1,2],[1,3],[2,5],[3,10],[5,100]),"Manganese-brass clad",8.10,26.5),
 rule("1 Dollar",2007,2020,"Presidential Dollar",["P","D","S"],prices([1,2],[1,2],[1,3],[2,5],[3,10],[5,100]),"Manganese-brass clad",8.10,26.5,[2017,2018,2019]),
 rule("1 Dollar",2018,2026,"American Innovation Dollar",["P","D","S"],prices([1,2],[1,2],[1,3],[2,5],[3,10],[5,100]),"Manganese-brass clad",8.10,26.5),
 rule("1 Dollar",2021,2026,"Morgan Dollar, Modern",["","S"],prices([50,90],[55,100],[60,120],[75,150],[100,250],[150,1000]),"99.9% silver",26.69,38.1,[2022]),
 rule("1 Dollar",2021,2026,"Peace Dollar, Modern",["","S"],prices([50,90],[55,100],[60,120],[75,150],[100,250],[150,1000]),"99.9% silver",26.69,38.1,[2022]),
]

def alert(denom,year,mint,name,instruction,potential,series="",variant="",p=None):
    item={"denomination":denom,"year":year,"mint_mark":mint,"series":series,"name":name,
          "variant":variant,"severity":"critical","instruction":instruction,"potential":potential,"source_url":PCGS}
    if p: item["prices"]=p
    return item

A=[
 alert("5c",1883,"","No CENTS Liberty Nickel","Check reverse for absence of CENTS; this is a recognized subtype, not automatically rare.","Popular subtype","Liberty Head"),
 alert("5c",1913,"","1913 Liberty Head Nickel","Only five are known; any candidate requires immediate expert authentication.","Legendary rarity","Liberty Head",p=prices([3000000,5000000],[3500000,5500000],[4000000,6000000],[4500000,6500000],[5000000,7000000],[6000000,10000000])),
 alert("5c",1916,"","Doubled die obverse","Inspect date and LIBERTY for strong separated doubling.","Major doubled die","Buffalo"),
 alert("5c",1918,"D","1918/7-D overdate","Inspect final date digits for the 7 beneath the 8.","Major overdate","Buffalo"),
 alert("5c",1937,"D","Three-legged Buffalo","Inspect the front foreleg and die-polish diagnostics.","Major recognized variety","Buffalo"),
 alert("5c",1943,"P","1943/2-P overdate","Inspect the 3 for remnants of a 2.","Major wartime variety","Jefferson"),
 alert("5c",2005,"D","Speared Bison","Inspect the bison for the strong die-gouge spear diagnostic.","Popular die variety","Jefferson"),
 alert("10c",1894,"S","1894-S Barber Dime","One of the great U.S. rarities; authenticate any candidate immediately.","Exceptional rarity","Barber",p=prices([1000000,1500000],[1200000,1800000],[1500000,2000000],[1800000,2500000],[2200000,3000000],[3000000,5000000])),
 alert("10c",1916,"D","1916-D Mercury Dime","Key date; authenticate the mintmark before assigning value.","Major key date","Mercury",p=prices([1200,1800],[1800,2600],[2500,4000],[4000,7000],[7000,15000],[18000,100000])),
 alert("10c",1942,"","1942/1 overdate","Inspect date for a 1 beneath the 2.","Major overdate","Mercury"),
 alert("10c",1942,"D","1942/1-D overdate","Inspect date for overdate diagnostics.","Major overdate","Mercury"),
 alert("10c",1968,"S","No S proof","A genuine proof without S is a major rarity.","Major proof error","Roosevelt"),
 alert("10c",1975,"S","No S proof","A genuine 1975 proof dime without S is an extreme rarity.","Extreme proof rarity","Roosevelt"),
 alert("10c",1982,"","No P mintmark","Philadelphia dimes missing the P are recognized errors.","Major mintmark error","Roosevelt"),
 alert("25c",1932,"D","1932-D key date","Authenticate mintmark and surfaces.","Major key date","Washington",p=prices([80,130],[120,190],[180,300],[275,500],[500,1000],[1200,15000])),
 alert("25c",1932,"S","1932-S key date","Authenticate mintmark and surfaces.","Major key date","Washington",p=prices([75,120],[110,180],[170,275],[250,450],[450,900],[1000,12000])),
 alert("25c",1965,"","Silver transitional error","Weigh and inspect edge; a genuine silver-planchet example needs authentication.","Major transitional error","Washington"),
 alert("25c",2004,"D","Wisconsin extra leaf","Inspect the corn stalk for high-leaf or low-leaf die varieties.","Popular state-quarter variety","State","Wisconsin"),
 alert("25c",2020,"W","West Point V75","Normal rare circulation issue; inspect obverse for V75 privy mark.","Scarce circulation issue","America"),
 alert("50c",1921,"D","1921-D key date","Authenticate mintmark and check for cleaning.","Major key date","Walking"),
 alert("50c",1964,"","Accented Hair proof","Inspect hair detail and missing serif diagnostics on proof coins.","Recognized proof variety","Kennedy"),
 alert("50c",1971,"D","40% silver transitional error","Inspect edge and weigh; a genuine silver-planchet strike requires authentication.","Major transitional error","Kennedy"),
 alert("50c",1974,"D","Doubled die obverse","Inspect motto, LIBERTY, and date for separated doubling.","Major doubled die","Kennedy"),
 alert("50c",1982,"P","No FG","Inspect reverse near the eagle's tail for missing designer initials and confirm die polishing.","Popular die variety","Kennedy"),
 alert("1 Dollar",1878,"","Eight tail feathers","Count eagle tail feathers and distinguish major 1878 Morgan reverse types.","Major subtype","Morgan"),
 alert("1 Dollar",1888,"O","Hot Lips doubled die","Inspect Liberty's lips and profile for strong doubling.","Major Morgan doubled die","Morgan"),
 alert("1 Dollar",1893,"S","1893-S Morgan","Major key date; authentication is essential.","Major key date","Morgan",p=prices([3000,4500],[4500,7000],[8000,14000],[18000,35000],[45000,90000],[150000,1000000])),
 alert("1 Dollar",1900,"O","O over CC","Inspect inside and around O for Carson City mintmark remnants.","Major over-mintmark","Morgan"),
 alert("1 Dollar",1921,"","High Relief Peace Dollar","Confirm high-relief diagnostics; this is the key first-year subtype.","Major subtype","Peace"),
 alert("1 Dollar",1972,"","Eisenhower reverse types","Identify Type 1, 2, or 3 Earth design; Type 2 is the key variety.","Major design variety","Eisenhower"),
 alert("1 Dollar",1979,"P","Wide Rim / Near Date","Inspect rim width and distance to the date.","Popular SBA variety","Susan"),
 alert("1 Dollar",2000,"P","Sacagawea mule and Wounded Eagle","Inspect for state-quarter obverse mule or die-gouge through eagle; authenticate candidates.","Major modern errors","Sacagawea"),
 alert("1 Dollar",2007,"P","Missing edge lettering","Check edge for absent date, mintmark, and motto.","Major Presidential error","Presidential"),
]

OUT.write_text(json.dumps({"schema_version":1,"updated_at":DATE,"rules":R,"alerts":A},separators=(",",":"))+"\n")
print(f"Wrote {len(R)} series rules and {len(A)} major alerts to {OUT}")
