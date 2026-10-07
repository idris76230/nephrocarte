"""Règles partagées : filtre néphro / oncologie, thématiques, détection PHRC."""
import re
ONCO = re.compile(r"(renal|kidney)\s+(\w+\s+){0,2}(carcinoma|cancer|tumou?r|neoplasm)|clear cell|renal cell|kidney cancer|renal cancer|kidney neoplasm|renal neoplasm|tumou?ral kidney|wilms|nephroblastoma|carcinoma|cancer|tumou?r|neoplasm|melanoma|sarcoma|lymphoma|leuka?emia|glioma|blastoma|malignan", re.I)
NEPH = re.compile(r"kidney|renal|(?<!epi)nephr|glomerul|dialys|uremi|uraemi|\bckd\b|\baki\b|\besrd\b|\beskd\b|iga\b|alport|fabry|cystinosis|fsgs|hyperoxaluria|lithiasis|kidney stone|\bc3g\b|\bahus\b|hemolytic uremic|anca|polyangiitis|hyperkal|proteinuri|albuminuri|tubulopath|hypophosphat|gitelman|bartter|thrombotic microangiopath|cystinuria|hemodiafiltration|hemofiltration|renal replacement|minimal change|podocyt|hepatorenal|nephrotox|urolog|bladder dysfunction|enuresis|adpkd|polycystic|vasculitis|rejection|organ transplant|(?<!pulmonary )(?<!portal )hypertension|ureter|dialytic", re.I)
def txt(*xs): return " | ".join(x for x in xs if x)
THEMES = [
 ("Transplantation", r"transplant|graft|allograft|rejection|donor|recipient|desensiti"),
 ("Dialyse / suppléance", r"dialys|hemodiafiltration|haemodiafiltration|end[- ]stage|\besrd\b|\beskd\b|kidney failure|renal replacement|arteriovenous fistula|vascular access|uremic pruritus"),
 ("Insuffisance rénale aiguë", r"acute kidney injury|\baki\b|acute renal|contrast[- ]induced|cardiac surgery associated|rhabdomyolysis"),
 ("Glomérulopathies / néphropathies immunes", r"glomerul|iga nephropathy|immunoglobulin a nephropathy|lupus nephritis|membranous|fsgs|nephrotic|minimal change|anca|polyangiitis|vasculitis|c3g|c3 glomerulopathy|hemolytic uremic|\bahus\b|thrombotic microangiopath|anti-gbm|goodpasture|complement|cryoglobulin"),
 ("Maladies rénales rares / génétiques", r"polycystic|adpkd|alport|fabry|cystinosis|hyperoxaluria|cystinuria|gitelman|bartter|tubulopath|hypophosphat|nephronophthisis|apol1|genetic|hereditary|rare"),
 ("MRC / néphroprotection / cardio-rénal", r"chronic kidney|\bckd\b|chronic renal|renal insufficiency|diabetic kidney|diabetic nephropathy|albuminuri|proteinuri|hyperkal|anemia|anaemia|hypertension|cardio|heart failure|mineral|phosph|hyperparathyroid|metabolic acidosis|sglt2|finerenone"),
 ("Lithiase / infections urinaires", r"lithiasis|kidney stone|renal colic|pyelonephritis|urinary tract infection"),
]
def theme(t):
    r = [n for n, p in THEMES if re.search(p, t, re.I)]
    return r or ["Autre néphrologie"]
PHRC = re.compile(r"phrc|programme hospitalier de recherche|hospital clinical research program|prme|preps|phrip|dgos|ministry of health,? france|minist[eè]re de la sant", re.I)
KCE = re.compile(r"\bkce\b|knowledge cent(er|re)|belgian health care knowledge", re.I)

PATHO = [
    # (thème, pathologie, motif)
    ("Glomérulopathies / néphropathies immunes", "Néphropathie à IgA", r"iga nephropathy|immunoglobulin a nephropathy|\bigan\b|berger|iga vasculitis|henoch"),
    ("Glomérulopathies / néphropathies immunes", "Néphropathie lupique", r"lupus"),
    ("Glomérulopathies / néphropathies immunes", "Glomérulonéphrite extramembraneuse", r"membranous"),
    ("Glomérulopathies / néphropathies immunes", "HSF / syndrome néphrotique", r"fsgs|focal segmental|nephrotic|minimal change|podocyt"),
    ("Glomérulopathies / néphropathies immunes", "Vascularites à ANCA", r"anca|polyangiitis|vasculitis|anti-gbm|goodpasture"),
    ("Glomérulopathies / néphropathies immunes", "MAT / SHU", r"hemolytic uremic|haemolytic uraemic|\bahus\b|\bshu\b|thrombotic microangiopath|\btma\b"),
    ("Glomérulopathies / néphropathies immunes", "Glomérulopathie à C3", r"c3 glomerulopathy|\bc3g\b|dense deposit|membranoproliferative"),
    ("Glomérulopathies / néphropathies immunes", "Gammapathies / amylose", r"amyloid|monoclonal gammopathy|mgrs|myeloma|light chain"),
    ("Transplantation", "Rejet / désimmunisation", r"rejection|desensiti|hla|donor-specific|\bdsa\b|antibody-mediated"),
    ("Transplantation", "Immunosuppression / tolérance", r"immunosuppress|tacrolimus|belatacept|tolerance|induction|steroid withdrawal|calcineurin"),
    ("Transplantation", "Infections post-greffe", r"cmv|cytomegalovirus|bk ?virus|polyomavirus|infection|vaccin"),
    ("Transplantation", "Donneur / préservation du greffon", r"donor|perfusion|preservation|delayed graft function|ischemia-reperfusion|machine"),
    ("Dialyse / suppléance", "Hémodialyse / HDF", r"hemodialysis|haemodialysis|hemodiafiltration|haemodiafiltration|\bhdf\b"),
    ("Dialyse / suppléance", "Dialyse péritonéale", r"peritoneal dialysis"),
    ("Dialyse / suppléance", "Abord vasculaire", r"fistula|vascular access|catheter|arteriovenous"),
    ("Dialyse / suppléance", "Complications du dialysé (prurit, CV, nutrition…)", r"pruritus|cardiovascular|nutrition|frailty|exercise|depression|quality of life|calciphylaxis"),
    ("MRC / néphroprotection / cardio-rénal", "Maladie rénale diabétique", r"diabet"),
    ("MRC / néphroprotection / cardio-rénal", "HTA / cardio-rénal", r"hypertension|heart failure|cardio"),
    ("MRC / néphroprotection / cardio-rénal", "Anémie", r"anemia|anaemia"),
    ("MRC / néphroprotection / cardio-rénal", "Hyperkaliémie / acidose", r"hyperkal|potassium|acidosis"),
    ("MRC / néphroprotection / cardio-rénal", "Troubles minéraux et osseux", r"phosph|parathyroid|mineral|bone|calcif|vitamin d"),
    ("MRC / néphroprotection / cardio-rénal", "Progression de la MRC", r"chronic kidney|\bckd\b|progression|egfr decline|albuminuri|proteinuri|sglt2|finerenone"),
    ("Maladies rénales rares / génétiques", "Polykystose (PKD)", r"polycystic|adpkd|arpkd"),
    ("Maladies rénales rares / génétiques", "Syndrome d'Alport", r"alport|collagen iv"),
    ("Maladies rénales rares / génétiques", "Maladie de Fabry", r"fabry"),
    ("Maladies rénales rares / génétiques", "Cystinose", r"cystinosis"),
    ("Maladies rénales rares / génétiques", "Hyperoxalurie", r"hyperoxaluria|oxalate"),
    ("Maladies rénales rares / génétiques", "Tubulopathies / hypophosphatémies", r"tubulopath|gitelman|bartter|hypophosphat|cystinuria|dent"),
    ("Insuffisance rénale aiguë", "IRA post-chirurgicale", r"cardiac surgery|surgery|postoperative|perioperative"),
    ("Insuffisance rénale aiguë", "IRA en réanimation / sepsis", r"sepsis|septic|intensive care|critically ill|\bicu\b|shock"),
    ("Insuffisance rénale aiguë", "Néphropathie aux produits de contraste / toxiques", r"contrast|nephrotox|rhabdomyolysis|cisplatin"),
    ("Lithiase / infections urinaires", "Lithiase", r"lithiasis|stone|colic"),
    ("Lithiase / infections urinaires", "Infections urinaires", r"pyelonephritis|urinary tract infection"),
]
